"""
This file is based on the code from https://github.com/JustAMan/pyWinClobber/blob/master/win32elevate.py

Copyright (c) 2013 by JustAMan at GitHub

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import os
import ctypes
import subprocess
from ctypes import c_ulong, c_char_p, c_int, c_void_p, POINTER, byref
from ctypes.wintypes import (
    HANDLE,
    BOOL,
    DWORD,
    HWND,
    HINSTANCE,
    HKEY,
    LPDWORD,
    SHORT,
    LPCWSTR,
    WORD,
    SMALL_RECT,
    LPCSTR,
)

from xonsh.lazyasd import lazyobject
from xonsh import lazyimps  # we aren't amalgamated in this module.
from xonsh import platform


__all__ = ("sudo",)


@lazyobject
def CloseHandle():
    ch = ctypes.windll.kernel32.CloseHandle
    ch.argtypes = (HANDLE,)
    ch.restype = BOOL
    return ch


@lazyobject
def GetActiveWindow():
    gaw = ctypes.windll.user32.GetActiveWindow
    gaw.argtypes = ()
    gaw.restype = HANDLE
    return gaw


TOKEN_READ = 0x20008


class ShellExecuteInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("fMask", c_ulong),
        ("hwnd", HWND),
        ("lpVerb", c_char_p),
        ("lpFile", c_char_p),
        ("lpParameters", c_char_p),
        ("lpDirectory", c_char_p),
        ("nShow", c_int),
        ("hInstApp", HINSTANCE),
        ("lpIDList", c_void_p),
        ("lpClass", c_char_p),
        ("hKeyClass", HKEY),
        ("dwHotKey", DWORD),
        ("hIcon", HANDLE),
        ("hProcess", HANDLE),
    ]

    def __init__(self, **kw):
        ctypes.Structure.__init__(self)
        self.cbSize = ctypes.sizeof(self)
        for field_name, field_value in kw.items():
            setattr(self, field_name, field_value)


@lazyobject
def ShellExecuteEx():
    see = ctypes.windll.Shell32.ShellExecuteExA
    PShellExecuteInfo = ctypes.POINTER(ShellExecuteInfo)
    see.argtypes = (PShellExecuteInfo,)
    see.restype = BOOL
    return see


@lazyobject
def WaitForSingleObject():
    wfso = ctypes