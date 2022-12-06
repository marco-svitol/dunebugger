import vlc, ctypes

instance = vlc.Instance()

# May work on some environments that Python uses same libc as libvlc
f = open('out.log', 'w')
instance.log_set_file(vlc.PyFile_AsFile(f))

# Or you should use raw `fopen` of the same version of libc instead
#fopen = ctypes.cdll.msvcrt.fopen
#fopen.restype = vlc.FILE_ptr
#fopen.argtypes = (ctypes.c_char_p, ctypes.c_char_p)
#f = fopen('out.log', 'w')
#instance.log_set_file(f)
