import asyncio
import os
import random
import textwrap
import tempfile

import aiohttp
import aiofiles
import discord
import img2pdf
import requests # keep for backward compatibility
from PIL import Image  # cuz alpha is a bitch
import os
import time
import zlib
from concurrent import futures
from . import consts 
#import consts  #if running locally 
aio_available = True

class Processor:
    def __init__(self, file_struct):
        self.crc = 0
        self.o_size = self.c_size = 0
        if file_struct['cmethod'] is None:
            self.process = self._process_through
            self.tail = self._no_tail
        elif file_struct['cmethod'] == 'deflate':
            self.compr = zlib.compressobj(5, zlib.DEFLATED, -15)
            self.process = self._process_deflate
            self.tail = self._tail_deflate

    # no compression
    def _process_through(self, chunk):
        self.o_size += len(chunk)
        self.c_size = self.o_size
        self.crc = zlib.crc32(chunk, self.crc)
        return chunk

    def _no_tail(self):
        return b''

    # deflate compression
    def _process_deflate(self, chunk):
        self.o_size += len(chunk)
        self.crc = zlib.crc32(chunk, self.crc)
        chunk = self.compr.compress(chunk)
        self.c_size += len(chunk)
        return chunk

    def _tail_deflate(self):
        chunk = self.compr.flush(zlib.Z_FINISH)
        self.c_size += len(chunk)
        return chunk

    # after processing counters and crc
    def state(self):
        return self.crc, self.o_size, self.c_size


class ZipBase:

    def __init__(self, files=[], chunksize=1024):
        """
        files - list of files, or generator returning files
                each file entry should be represented as dict with
                parameters:
                file - full path to file name
                name - (optional) name of file in zip archive
                       if not used, filename stripped from 'file' will be used
                stream - (optional) can be used as replacement for 'file'
                         entry, will be treated as generator returnig
                         chunks of data that will be streamed in archive.
                         If used, then 'name' entry is required.
        chunksize - default size of data block streamed from files
        """
        self._source_of_files = files
        self.__files = []
        self.__version = consts.ZIP32_VERSION
        self.zip64 = False
        self.chunksize = chunksize
        # this flag tuns on signature for data descriptor record.
        # see section 4.3.9.3 of ZIP File Format Specification
        self.__use_ddmagic = True
        # central directory size and placement
        self.__cdir_size = self.__offset = 0

    def zip64_required(self):
        """
        Turn on zip64 mode for archive
        """
        raise NotImplementedError("Zip64 is not supported yet")

    def _create_file_struct(self, data):
        """
        extract info about streamed file and return all processed data
        required in zip archive
        """
        # date and time of file
        dt = time.localtime()
        dosdate = ((dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]) \
            & 0xffff
        dostime = (dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)) \
            & 0xffff

        # check zip32 limit
        # stats = os.stat(data['file'])
        #  if stats.st_size > consts.ZIP32_LIMIT:
        #     self.zip64_required()
        # file properties used in zip
        file_struct = {'mod_time': dostime,
                       'mod_date': dosdate,
                       'crc': 0,  # will be calculated during data streaming
                       "offset": 0,  # file header offset in zip file
                       'flags': 0b00001000}  # flag about using data descriptor is always on

        if 'file' in data:
            file_struct['src'] = data['file']
            file_struct['stype'] = 'f'
        elif 'stream' in data:
            file_struct['src'] = data['stream']
            file_struct['stype'] = 's'
        else:
            raise Exception('No file or stream in sources')

        cmpr = data.get('compression', None)
        if cmpr not in (None, 'deflate'):
            raise Exception('Unknown compression method %r' % cmpr)
        file_struct['cmethod'] = cmpr
        file_struct['cmpr_id'] = {
            None: consts.COMPRESSION_STORE,
            'deflate': consts.COMPRESSION_DEFLATE}[cmpr]

        # file name in archive
        if 'name' not in data:
            data['name'] = os.path.basename(data['file'])
        try:
            file_struct['fname'] = data['name'].encode("ascii")
        except UnicodeError:
            file_struct['fname'] = data['name'].encode("utf-8")
            file_struct['flags'] |= consts.UTF8_FLAG
        return file_struct

    # zip structures creation

    def _make_extra_field(self, signature, data):
        """
        Extra field for file
        """
        fields = {"signature": signature,
                  "size": len(data)}
        head = consts.EXTRA_TUPLE(**fields)
        head = consts.EXTRA_STRUCT.pack(*head)
        return head + data

    def _make_local_file_header(self, file_struct):
        """
        Create file header
        """
        fields = {"signature": consts.LF_MAGIC,
                  "version": self.__version,
                  "flags": file_struct['flags'],
                  "compression": file_struct['cmpr_id'],
                  "mod_time": file_struct['mod_time'],
                  "mod_date": file_struct['mod_date'],
                  "crc": 0,
                  "uncomp_size": 0,
                  "comp_size": 0,
                  "fname_len": len(file_struct['fname']),
                  "extra_len": 0}
        head = consts.LF_TUPLE(**fields)
        head = consts.LF_STRUCT.pack(*head)
        head += file_struct['fname']
        return head

    def _make_data_descriptor(self, file_struct, crc, org_size, compr_size):
        """
        Create file descriptor.
        This function also updates size and crc fields of file_struct
        """
        # hack for making CRC unsigned long
        file_struct['crc'] = crc & 0xffffffff
        file_struct['size'] = org_size
        file_struct['csize'] = compr_size
        fields = {"uncomp_size": file_struct['size'],
                  "comp_size": file_struct['csize'],
                  "crc": file_struct['crc']}
        descriptor = consts.DD_TUPLE(**fields)
        descriptor = consts.DD_STRUCT.pack(*descriptor)
        if self.__use_ddmagic:
            descriptor = consts.DD_MAGIC + descriptor
        return descriptor

    def _make_cdir_file_header(self, file_struct):
        """
        Create central directory file header
        """
        fields = {"signature": consts.CDFH_MAGIC,
                  "system": 0x03,  # 0x03 - unix
                  "version": self.__version,
                  "version_ndd": self.__version,
                  "flags": file_struct['flags'],
                  "compression": file_struct['cmpr_id'],
                  "mod_time": file_struct['mod_time'],
                  "mod_date": file_struct['mod_date'],
                  "uncomp_size": file_struct['size'],
                  "comp_size": file_struct['csize'],
                  "offset": file_struct['offset'],  # < file header offset
                  "crc": file_struct['crc'],
                  "fname_len": len(file_struct['fname']),
                  "extra_len": 0,
                  "fcomm_len": 0,  # comment length
                  "disk_start": 0,
                  "attrs_int": 0,
                  "attrs_ext": 0}
        cdfh = consts.CDLF_TUPLE(**fields)
        cdfh = consts.CDLF_STRUCT.pack(*cdfh)
        cdfh += file_struct['fname']
        return cdfh

    def _make_cdend(self):
        """
        make end of central directory record
        """
        fields = {"signature": consts.CD_END_MAGIC,
                  "disk_num": 0,
                  "disk_cdstart": 0,
                  "disk_entries": len(self.__files),
                  "total_entries": len(self.__files),
                  "cd_size": self.__cdir_size,
                  "cd_offset": self._offset_get(),
                  "comment_len": 0}
        cdend = consts.CD_END_TUPLE(**fields)
        cdend = consts.CD_END_STRUCT.pack(*cdend)
        return cdend

    def _make_end_structures(self):
        """
        cdir and cdend structures are saved at the end of zip file
        """
        # stream central directory entries
        for idx, file_struct in enumerate(self.__files):
            chunk = self._make_cdir_file_header(file_struct)
            self.__cdir_size += len(chunk)
            yield chunk
        # stream end of central directory
        yield self._make_cdend()

    def _offset_add(self, value):
        self.__offset += value

    def _offset_get(self):
        return self.__offset

    def _add_file_to_cdir(self, file_struct):
        self.__files.append(file_struct)

    def _cleanup(self):
        """
        Clean all structs after streaming
        """
        self.__files = []
        self.__cdir_size = self.__offset = 0


class AioZipStream(ZipBase):
    """
    Asynchronous version of ZipStream
    """

    def __init__(self, *args, **kwargs):
        super(AioZipStream, self).__init__(*args, **kwargs)

    def __get_executor(self):
        # get thread pool executor
        try:
            return self.__tpex
        except AttributeError:
            self.__tpex = futures.ThreadPoolExecutor(max_workers=1)
            return self.__tpex

    async def _execute_aio_task(self, task, *args, **kwargs):
        # run synchronous task in separate thread and await for result
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.__get_executor(),
                                          task, *args, **kwargs)

    def _create_file_struct(self, data):
        if 'file' in data:
            if not aio_available:
                raise Exception(
                    "aiofiles module is required to stream files asynchronously")
        return super(AioZipStream, self)._create_file_struct(data)

    async def data_generator(self, src, src_type):
        if src_type == 's':
            async for chunk in src:
                yield chunk
            return
        if src_type == 'f':
            async with aiofiles.open(src, "rb") as fh:
                while True:
                    part = await fh.read(self.chunksize)
                    if not part:
                        break
                    yield part
            return

    async def _stream_single_file(self, file_struct):
        """
        stream single zip file with header and descriptor at the end
        """
        yield self._make_local_file_header(file_struct)
        pcs = Processor(file_struct)
        async for chunk in self.data_generator(file_struct['src'], file_struct['stype']):
            yield await self._execute_aio_task(pcs.process, chunk)
        chunk = await self._execute_aio_task(pcs.tail)
        # chunk = await pcs.aio_tail()
        if len(chunk) > 0:
            yield chunk
        yield self._make_data_descriptor(file_struct, *pcs.state())

    async def stream(self):
        # stream files
        for idx, source in enumerate(self._source_of_files):
            file_struct = self._create_file_struct(source)
            # file offset in archive
            file_struct['offset'] = self._offset_get()
            self._add_file_to_cdir(file_struct)
            # file data
            async for chunk in self._stream_single_file(file_struct):
                self._offset_add(len(chunk))
                yield chunk
        # stream zip structures
        for chunk in self._make_end_structures():
            yield chunk
        self._cleanup()

colors = [0, 1752220, 3066993, 3447003, 10181046, 15844367, 15105570, 15158332,
          9807270, 8359053, 3426654, 1146986, 2067276, 2123412, 7419530, 12745742,
          11027200, 10038562, 9936031, 12370112, 2899536, 16580705, 12320855]


def with_session(func):
    async def wrapper(*args, **kwargs):
        async with aiohttp.ClientSession(headers={"User-Agent": "Montana/1.0"}) as session:
            result = await func(session, *args, **kwargs)
        return result
    return wrapper


def wrapped(s):
    wrapper = textwrap.TextWrapper(width=32)
    word_list = wrapper.wrap(text=s)
    s = ""
    for word in word_list:
        s += '\n' + word
    return s


def time_format(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return days, hours, minutes, seconds


def pretty_time_format(seconds, *, shorten=False, only_most_significant=False, always_seconds=False):
    days, hours, minutes, seconds = time_format(seconds)
    timespec = [
        (days, 'day', 'days'),
        (hours, 'hour', 'hours'),
        (minutes, 'minute', 'minutes'),
    ]
    timeprint = [(cnt, singular, plural) for cnt, singular, plural in timespec if cnt]
    if not timeprint or always_seconds:
        timeprint.append((seconds, 'second', 'seconds'))
    if only_most_significant:
        timeprint = [timeprint[0]]

    def format_(triple):
        cnt, singular, plural = triple
        return f'{cnt}{singular[0]}' if shorten else f'{cnt} {singular if cnt == 1 else plural}'

    return ' '.join(map(format_, timeprint))


def make_embed(text):
    return discord.Embed(description=str(text), color=random.choice(colors))


async def filesender(file_name=None):
    async with aiofiles.open(file_name, 'rb') as f:
        chunk = await f.read(64*1024)
        while chunk:
            yield chunk
            chunk = await f.read(64*1024)


@with_session
async def upload(session, name):
    async with session.get('https://apiv2.gofile.io/getServer') as resp:
        data = await resp.json()
        server = data['data']['server']
    upload_uri = f'https://{server}.gofile.io/uploadFile'
    postdata = aiohttp.FormData()
    postdata.add_field(
        'file',
        filesender(name),
        filename=name,
        content_type='application/pdf'
    )
    async with session.post(upload_uri, data=postdata) as resp:
        data = await resp.json()
        code = data['data']['code']
    return f"https://gofile.io/?c={code}"


async def makepdf(links, name):  # low memory usage but slow af
    images = []
    img_num = 1
    for link in links:
        response = requests.head(link, allow_redirects=True)
        size = int(response.headers.get('content-length', -1))
        if size < 5000000:
            img = open(name + str(img_num) + ".wtf", "wb")
            img.write(requests.get(link).content)
            img.close()
            images.append(name + str(img_num) + ".wtf")
            img_num += 1
    filename = f'{name}_{img_num}.pdf'
    pdf = open(filename, "wb")
    pdf.write(img2pdf.convert(images))
    pdf.close()
    for i in images:
        os.remove(i)
    return filename


async def fastmakepdf(links, name):  # super high memory usage but fast
    images = []
    for link in links:
        response = requests.head(link, allow_redirects=True)
        size = int(response.headers.get('content-length', -1))
        if size < 5000000:
            images.append(Image.open(requests.get(link, stream=True).raw).convert('RGB'))
    filename = f'{name}.pdf'
    images[0].save(filename, save_all=True, append_images=images[1:])
    for i in images:
        i.close()
    return filename


@with_session
async def async_makepdf(session, links, name):
    with tempfile.TemporaryDirectory() as tempdir:
        files = []
        for i, link in enumerate(links):
            async with session.head(link, allow_redirects=True) as resp:
                size = int(resp.headers.get('Content-Length', -1))
            if size > 5e6:  # 5 MB
                continue
            image_filename = f'{tempdir}/{i}.idk'
            async with session.get(link) as resp:
                content = await resp.content.read()
            imgio = img2pdf.BytesIO(content)
            image = Image.open(imgio).convert('RGB')
            # Unknown ExifOrientationError on PNG format
            image.save(image_filename, format='JPEG')
            files.append(image_filename)
        filename = f'{name}.pdf'
        async with aiofiles.open(filename, mode='wb') as file:
            await file.write(img2pdf.convert(files))
    return filename


_pdfsem = asyncio.Semaphore(2)
async def send_pdf(ctx, name, links):
    if len(name) > 25:
        name = name[:20]
    originalname = name
    loading = await ctx.send(file=discord.File('static/loading.gif'))
    async with _pdfsem:
        name += str(random.randint(0, 1000000000))
        filename = await async_makepdf(links, name)
        # if len(links) > 50:
        #     filename = await makepdf(links, name)
        # else:
        #     filename = await fastmakepdf(links, name)
        url = await upload(filename)
        embed = discord.Embed(
            title=originalname,
            description="",
            color=random.choice(colors),
            url=url
        )
        await ctx.send(embed=embed)
        os.remove(filename)
        await loading.delete()


async def async_zip(filename, files):
    # larger chunk size will increase performance
    aiozip = AioZipStream(files, chunksize=32768)
    async with aiofiles.open(filename, mode='wb') as z:
        async for chunk in aiozip.stream():
            await z.write(chunk)

@with_session
async def async_makezip(session, links, name):
    with tempfile.TemporaryDirectory() as tempdir:
        files = []
        for i, link in enumerate(links):
            async with session.head(link, allow_redirects=True) as resp:
                size = int(resp.headers.get('Content-Length', -1))
            if size > 5e6:  # 5 MB
                continue
            image_filename = f'{tempdir}/{i}.idk'
            async with session.get(link) as resp:
                content = await resp.content.read()
            imgio = img2pdf.BytesIO(content)
            image = Image.open(imgio).convert('RGB')
            # Unknown ExifOrientationError on PNG format
            image.save(image_filename, format='JPEG')
            files.append({'file' : image_filename , 'name' : name + image_filename[ : -4] + '.jpg'})
        filename = f'{name}.zip'
        await async_zip(filename, files)
    return filename

_zipsem = asyncio.Semaphore(2)
async def send_zip(ctx, name, links):
    if len(name) > 25:
        name = name[:20]
    originalname = name
    loading = await ctx.send(file=discord.File('static/loading.gif'))
    async with _zipsem:
        name += str(random.randint(0, 1000000000))
        filename = await async_makezip(links, name)
        url = await upload(filename)
        embed = discord.Embed(
            title=originalname,
            description="",
            color=random.choice(colors),
            url=url
        )
        await ctx.send(embed=embed)
        os.remove(filename)
        await loading.delete()

def fib(n):
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
    return a


def has_any_strrole(seq, *roles):
    return any(r.name in roles for r in seq)


def filter_bots(members):
    return [m for m in members if not m.bot]
