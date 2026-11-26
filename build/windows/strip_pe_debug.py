"""Remove PE debug directory and payloads; leave executable code/relocations intact."""
from pathlib import Path
import struct,sys
def strip(path):
    data=bytearray(path.read_bytes());pe=struct.unpack_from('<I',data,0x3c)[0]
    if data[pe:pe+4]!=b'PE\0\0':raise ValueError(path)
    count=struct.unpack_from('<H',data,pe+6)[0]
    opt=pe+24;optlen=struct.unpack_from('<H',data,pe+20)[0]
    magic=struct.unpack_from('<H',data,opt)[0]
    directory=opt+(112 if magic==0x20b else 96)+6*8
    rva,size=struct.unpack_from('<II',data,directory)
    if not rva:return False
    for i in range(count):
        sec=opt+optlen+i*40
        virtualsize,start,rawsize,raw=struct.unpack_from('<IIII',data,sec+8)
        if start<=rva<start+max(virtualsize,rawsize):
            pos=raw+rva-start
            for entry in range(pos,pos+size,28):
                payloadsize,_,pointer=struct.unpack_from('<III',data,entry+16)
                if pointer and payloadsize:
                    assert pointer+payloadsize<=len(data)
                    data[pointer:pointer+payloadsize]=b'\0'*payloadsize
            data[pos:pos+size]=b'\0'*size
            data[directory:directory+8]=b'\0'*8
            struct.pack_into('<I',data,opt+64,0) # No Authenticode signature/checksum is claimed.
            path.write_bytes(data);return True
    raise ValueError('Unmapped debug directory: '+str(path))
if __name__=='__main__':
    root=Path(sys.argv[1]);changed=sum(strip(p) for p in root.rglob('*.pyd'))
    print('Stripped native modules:',changed)
