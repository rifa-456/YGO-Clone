# cython: language_level=3, embedsignature=True

cdef class Color:
    def __cinit__(self, double r=0.0, double g=0.0, double b=0.0, double a=1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @staticmethod
    def hex(int hex_val):
        return Color(
            ((hex_val >> 16) & 0xFF) / 255.0,
            ((hex_val >> 8) & 0xFF) / 255.0,
            (hex_val & 0xFF) / 255.0
        )

    cpdef tuple to_u8(self):
        return (
            int(self.r * 255),
            int(self.g * 255),
            int(self.b * 255),
            int(self.a * 255)
        )

    cpdef Color lerp(self, Color to, double weight):
        return Color(
            self.r + (to.r - self.r) * weight,
            self.g + (to.g - self.g) * weight,
            self.b + (to.b - self.b) * weight,
            self.a + (to.a - self.a) * weight,
        )

    def __repr__(self):
        return f"Color({self.r:.2f}, {self.g:.2f}, {self.b:.2f}, {self.a:.2f})"