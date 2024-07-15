"""Compute module backplane communication."""

import ctypes
from pathlib import Path

import numpy as np

DLL_PATH = str(Path(__file__).parent / "libcompute.dll")


cip_dtypes = {
    "BOOL": (0xC1, 1, np.bool_),
    "SINT": (0xC2, 1, np.int8),
    "INT": (0xC3, 2, np.int16),
    "DINT": (0xC4, 4, np.int32),
    "LINT": (0xC5, 8, np.int64),
    "USINT": (0xC6, 1, np.uint8),
    "UINT": (0xC7, 2, np.uint16),
    "UDINT": (0xC8, 4, np.uint32),
    "ULINT": (0xC9, 8, np.uint64),
    "REAL": (0xCA, 4, np.float32),
    "LREAL": (0xCB, 8, np.float64),
    "BYTE": (0xD1, 1, np.uint8),
    "WORD": (0xD2, 2, np.uint16),
    "DWORD": (0xD3, 4, np.uint32),
    "LWORD": (0xD4, 8, np.uint64),
    "STRING": (0x0FCE, 88, np.dtype("i4, S82, i2")),
}  # string82


error_code_dict = {
    0: "SUCCESS",  # Function returned successfully
    1: "ERROR_BADPARAM",  # A parameter is invalid
    2: "ERROR_REOPEN",  # Device is already open
    3: "ERROR_NODEVICE",  # Device is not present
    4: "ERROR_NOACCESS",  # Invalid access
    5: "ERROR_TIMEOUT",  # The function has timed out
    6: "ERROR_MSGTOOBIG",  # The message is too large
    7: "ERROR_BADCONFIG",  # The IO is not configured properly
    8: "ERROR_MEMALLOC",  # Unable to allocate memory
    9: "ERROR_NOTSUPPORTED",  # Function is not supported on this platform
    10: "ERROR_ALREADY_REGISTERED",  # Object is already registered
    11: "ERROR_INVALID_OBJHANDLE",  # Object handle is not valid
    12: "ERROR_NODATA",  # No data has been received yet
    13: "ERROR_INVALID",  # Invalid function for current state / config
    14: "ERROR_BUSY",  # Device is busy - retry function
    15: "ERROR_REINIT",  # Failed because already initialized
    16: "ERROR_NOINIT",  # Failed because not initialized
    17: "ERROR_DATAOVFL",  # Data overflow
    18: "ERROR_DATAUVFL",  # Data underflow
    19: "ERROR_DATAINCONSIST",  # Inconsistent data error
    20: "ERROR_VERMISMATCH",  # Version mismatch
    21: "ERROR_OBJEMPTY",  # Object empty
    22: "ERROR_PCCC",  # PCCC error
    23: "ERROR_RESET_REFUSED",  # Application refused the ID reset request
    24: "ERROR_RESET_APP_GEN",  # Application will reset when it is ready
    25: "ERROR_REQUEST_ID_LEN",  # Requestor ID length error
    26: "ERROR_VENDOR_ID",  # Vendor ID mismatch
    27: "ERROR_SERIAL_NUM",  # Serial number mismatch
    28: "ERROR_COMMAND_BYTE",  # Command byte mismatch
    29: "ERROR_TNSW",  # TNSW mismatch
    30: "ERROR_LOCAL_STS",  # Local STS error indicated
    31: "ERROR_RESET_SUCCESS",  # Application will handle the reset request
    100: "ERROR_REMOTE_STS_OFFSET",  # Raw error code; see ocxbpapi.h for details
    115: "ERROR_REMOTE_EXTSTS_OFFSET",  # Raw error code; see ocxbpapi.h
}


class Compute:
    """
    Compute class -- Python wrapper for OCX library to interface with
    1756-Compute modules.
    """

    led_states = {"off": 0, "green": 1, "red": 2, "yellow": 3}

    def __init__(self, timeout_ms=2500):
        """
        Contructor; initializes the C shared library and opens the connection.

        Arguments:
            timeout_ms -- the timeout, in milliseconds, for reading/writing tags
        """
        self.timeout_ms = timeout_ms
        self._init_library()
        self._open()
        if self.handle:
            self.active_handle = True

    def __del__(self):
        """Destructor"""
        self.close()

    def _init_library(self):
        """
        Initializes the OCX shared library and sets argument types and return
        codes (note that the default return code is a C int).
        """
        self.lib = ctypes.cdll.LoadLibrary(DLL_PATH)
        self.lib.open.restype = ctypes.c_uint
        self.lib.access_tag.argtypes = [
            ctypes.c_uint,
            ctypes.c_char_p,
            ctypes.c_ushort,
            ctypes.c_void_p,
            ctypes.c_ushort,
            ctypes.c_ushort,
            ctypes.c_bool,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        self.lib.get_led.argtypes = [ctypes.c_uint, ctypes.c_int]
        self.lib.set_led.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_int]
        self.lib.get_display.argtypes = [ctypes.c_uint, ctypes.c_char_p]
        self.lib.set_display.argtypes = [ctypes.c_uint, ctypes.c_char_p]

    def _error_handler(self, error_code):
        """Processes return codes from the OCX C library."""
        if error_code == 0:
            return
        # error_tuple = (inspect.stack()[1][3], error_code_dict[error_code])
        # raise RuntimeError("%s returned error code: %s" % error_tuple)
        raise RuntimeError(
            "returned error code: %d, %s" % (error_code, error_code_dict[error_code])
        )

    def _open(self):
        """
        Opens the connection to the compute module.
        This function is called automatically by the constructor.
        """
        self.handle = self.lib.open()
        if self.handle < 0:
            ec = -self.handle
            self.handle = None
            self._error_handler(ec)

    def close(self):
        """
        Closes the connection to the compute module.

        This method is called automatically by the destructor, but it is still
        recommended to call it explicitly once the connection is no longer
        needed.
        """
        if self.active_handle:
            ec = self.lib.close(self.handle)
            if ec == 0:
                self.active_handle = False
            else:
                self._error_handler(ec)

    def read_tag(self, tag_name: str, cip_dtype: str, length: int, slot: str):
        """
        Reads value(s) from a tag stored in a local Logix controller.

        The tag name can be formatted as follows (non-exhaustive examples):
        * tag_name
        * array_tag[x]
        * struct_tag.member

        The cip_dtype is an IEC 61131-3 data type -- see the cip_dtypes
        dictionary defined in this module.

        The length argument is 1 (default) for a single element, or the number
        of elements to be read from a 1D array. More complicated data types
        (e.g., 2D arrays, structs) are not currently supported.

        Note that a string is considered a single element, and is limited to 82
        characters by the OCX library.

        The slot argument defines the address of the Logix controller where the
        tag is located (default: 0).
        """
        cip_dtype = cip_dtype.upper()
        data_type, element_size, buf_dtype = cip_dtypes[cip_dtype]
        buffer = np.zeros(length, dtype=buf_dtype)
        b_tag_name = tag_name.encode("utf-8")
        b_slot = slot.encode("utf-8")
        ec = self.lib.access_tag(
            self.handle,
            b_tag_name,
            data_type,
            buffer.ctypes.data,
            element_size,
            length,
            True,
            b_slot,
            self.timeout_ms,
        )
        self._error_handler(ec)
        if any(d in cip_dtype for d in ["WORD", "BYTE"]):
            return bytes(buffer)
        if cip_dtype == "STRING":
            buffer = [x[1].decode("utf-8") for x in buffer]
        if length == 1:
            return buffer[0]
        else:
            return buffer

    def write_tag(self, tag_name: str, cip_dtype: str, data, slot: str):
        """
        Writes value(s) to a tag stored in a local Logix controller.

        The tag name can be formatted as follows (non-exhaustive examples):
        * tag_name
        * array_tag[x]
        * struct_tag.member

        The cip_dtype is an IEC 61131-3 data type -- see the cip_dtypes
        dictionary defined in this module.

        Data is either a single element or 1D array. More complicated data
        types (e.g., 2D arrays, structs) are not currently supported.

        Note that a string is considered a single element, and is limited to 82
        characters by the OCX library.

        The slot argument defines the address of the Logix controller where the
        tag is located (default: 0).
        """
        cip_dtype = cip_dtype.upper()
        data_type, element_size, buf_dtype = cip_dtypes[cip_dtype]
        b_tag_name = tag_name.encode("utf-8")
        b_slot = slot.encode("utf-8")
        if cip_dtype == "STRING":
            if isinstance(data, str):
                buffer = np.array((len(data), data, 0), dtype=buf_dtype)
                length = 1
            else:
                string_tuples = [(len(s), s, 0) for s in data]
                buffer = np.array(string_tuples, dtype=buf_dtype)
                length = len(buffer)
        else:
            buffer = np.array([data], dtype=buf_dtype).flatten()
            length = len(buffer)
        ec = self.lib.access_tag(
            self.handle,
            b_tag_name,
            data_type,
            buffer.ctypes.data,
            element_size,
            length,
            False,
            b_slot,
            self.timeout_ms,
        )
        self._error_handler(ec)

    def get_led(self, idx):
        """
        Gets the state of one of the compute module's 4 status LEDs, indexed as:
            0 = OK
            1 = User 1
            2 = User 2
            3 = User 3

        The state is given as a string, and can be any of the following:
        off, green, red, or yellow.
        """
        assert idx in range(4)
        int_state = self.lib.get_led(self.handle, idx)
        if int_state not in self.led_states.values():
            self._error_handler(-int_state)
        return list(self.led_states.keys())[int_state]

    def set_led(self, idx, state):
        """
        Set one of the compute module's 4 status LEDs, indexed as:
            0 = OK
            1 = User 1
            2 = User 2
            3 = User 3

        The state should be provided as a string. The following are valid:
        off, green, red, or yellow.
        """
        assert idx in range(4)
        int_state = self.led_states[state]
        ec = self.lib.set_led(self.handle, idx, int_state)
        self._error_handler(ec)

    def get_display(self):
        """Reads the contents of the compute module's 4-character display."""
        buffer = ctypes.create_string_buffer(5)
        ec = self.lib.get_display(self.handle, buffer)
        self._error_handler(ec)
        return buffer.value.decode("utf-8")

    def set_display(self, data):
        """
        Writes a string to the compute module's 4-character display.
        Strings longer than 4 characters are automatically truncated.

        Note: The display will be reset when the connection to the controller
              is closed (i.e., when close() is called or this class goes out
              of scope).
        """
        buffer = ctypes.create_string_buffer(data[:4].encode("utf-8"), 5)
        ec = self.lib.set_display(self.handle, buffer)
        self._error_handler(ec)
