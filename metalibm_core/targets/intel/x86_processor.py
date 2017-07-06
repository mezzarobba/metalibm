# -*- coding: utf-8 -*-

###############################################################################
# This file is part of Kalray's Metalibm tool
# Copyright (2014)
# All rights reserved
# created:          Apr 11th,  2014
# last-modified:    Nov  6th,  2014
#
# author(s): Nicolas Brunie (nicolas.brunie@kalray.eu)
###############################################################################

from metalibm_core.utility.log_report import *
from metalibm_core.code_generation.generator_utility import *
from metalibm_core.code_generation.complex_generator import ComplexOperator
from metalibm_core.core.ml_formats import *
from metalibm_core.core.ml_complex_formats import ML_Pointer_Format
from metalibm_core.core.ml_operations import *
from metalibm_core.code_generation.generic_processor import GenericProcessor
from metalibm_core.core.target import TargetRegister
from metalibm_core.core.ml_table import ML_TableFormat

from metalibm_core.targets.common.vector_backend import VectorBackend

## format for a single fp32 stored in a XMM 128-bit register
ML_SSE_m128_v1float32  = ML_FormatConstructor(128, "__m128",  None, lambda v: None)
## format for packed 4 fp32 in a XMM 128-bit register
ML_SSE_m128_v4float32  = ML_FormatConstructor(128, "__m128",  None, lambda v: None)
## format for single 1 fp64 in a XMM 128-bit register
ML_SSE_m128_v1float64 = ML_FormatConstructor(128, "__m128d", None, lambda v: None)
## format for packed 2 fp64 in a XMM 128-bit register
ML_SSE_m128_v2float64 = ML_FormatConstructor(128, "__m128d", None, lambda v: None)
## format for a single int32 stored in a XMM 128-bit register
ML_SSE_m128_v1int32  = ML_FormatConstructor(128, "__m128i",  None, lambda v: None)
## format for packed 4 int32 in a XMM 128-bit register
ML_SSE_m128_v4int32  = ML_FormatConstructor(128, "__m128i",  None, lambda v: None)
## format for single 1 int64 in a XMM 128-bit register
ML_SSE_m128_v1int64  = ML_FormatConstructor(128, "__m128i",  None, lambda v: None)
## format for packed 2 int64 in a XMM 128-bit register
ML_SSE_m128_v2int64  = ML_FormatConstructor(128, "__m128i",  None, lambda v: None)

## format for packed 8 fp32 in a YMM 256-bit register
ML_AVX_m256_v8float32 = ML_FormatConstructor(256, "__m256",  None, lambda v: None)
## format for packed 4 fp64 in a YMM 256-bit register
ML_AVX_m256_v4float64 = ML_FormatConstructor(256, "__m256d", None, lambda v: None)
## format for packed 8 int32 in a YMM 256-bit register
ML_AVX_m256_v8int32   = ML_FormatConstructor(256, "__m256i", None, lambda v: None)
## format for packed 4 int64 in a YMM 256-bit register
ML_AVX_m256_v4int64   = ML_FormatConstructor(256, "__m256i", None, lambda v: None)

# Conversion function from any float to a float packed into a __m128 register
_mm_set_ss = FunctionOperator("_mm_set_ss", arity = 1, force_folding = True, output_precision = ML_SSE_m128_v1float32, require_header = ["xmmintrin.h"])

_mm_set1_epi32 = FunctionOperator("_mm_set1_epi32", arity = 1, force_folding = True, output_precision = ML_SSE_m128_v1int32, require_header = ["xmmintrin.h"])

_mm_set1_epi64x = FunctionOperator("_mm_set1_epi64x", arity = 1, force_folding = True, output_precision = ML_SSE_m128_v4int32, require_header = ["emmintrin.h"])

# Conversion of a scalar float contained in a __m128 registers to a signed integer
# contained also in a __m128 register
_mm_cvt_ss2si = FunctionOperator("_mm_cvt_ss2si", arity = 1, require_header = ["xmmintrin.h"])

_mm_cvtsd_si64  = FunctionOperator("_mm_cvtsd_si64", arity = 1, require_header = ["emmintrin.h"])
_mm_cvtsd_si32  = FunctionOperator("_mm_cvtsd_si32", arity = 1, require_header = ["emmintrin.h"])

_mm_round_ss_rn = FunctionOperator("_mm_round_ss", arg_map = {0: FO_Arg(0), 1: FO_Arg(0), 2: "_MM_FROUND_TO_NEAREST_INT"}, arity = 1, output_precision = ML_SSE_m128_v1float32
, require_header = ["smmintrin.h"])
_mm_cvtss_f32 = FunctionOperator("_mm_cvtss_f32", arity = 1, output_precision = ML_Binary32, require_header = ["xmmintrin.h"])

_mm_set_sd = FunctionOperator("_mm_set_sd", arity = 1, force_folding = True,
                              output_precision = ML_SSE_m128_v1float64,
                              require_header = ["xmmintrin.h"])
_mm_round_sd_rn = FunctionOperator("_mm_round_sd", arg_map = {0: FO_Arg(0), 1: FO_Arg(0), 2: "_MM_FROUND_TO_NEAREST_INT"}, arity = 1, output_precision = ML_SSE_m128_v1float64, require_header = ["smmintrin.h"])
_mm_cvtsd_f64 = FunctionOperator("_mm_cvtsd_f64", arity = 1, output_precision = ML_Binary64, require_header = ["xmmintrin.h"])


## Wrapper for intel x86_sse intrinsics
#  defined in <xmmintrin.h> header
def XmmIntrin(*args, **kw):
  kw.update({
    'require_header': ["xmmintrin.h"]
  })
  return FunctionOperator(*args, **kw)
## Wrapper for intel x86_sse2 intrinsics
#  defined in <emmintrin.h> header
def EmmIntrin(*args, **kw):
  kw.update({
    'require_header': ["emmintrin.h"]
  })
  return FunctionOperator(*args, **kw)
## Wrapper for intel x86_ssse3 intrinsics
#  defined in <tmmintrin.h> header
def TmmIntrin(*args, **kw):
  kw.update({
    'require_header': ["tmmintrin.h"]
  })
  return FunctionOperator(*args, **kw)
## Wrapper for intel x86 sse4.1 intrinsics
#  defined in <smmintrin.h> header
def SmmIntrin(*args, **kw):
  kw.update({
    'require_header': ["smmintrin.h"]
  })
  return FunctionOperator(*args, **kw)
## Wrapper for intel x86_avx2 intrinsics
#  defined in <immintrin.h> header
def ImmIntrin(*args, **kw):
  kw.update({
    'require_header': ["immintrin.h"]
  })
  return FunctionOperator(*args, **kw)


# 3-to-5-cycle latency / 1-to-2-cycle throughput approximate reciprocal, with a
# maximum relative error of 1.5 * 2^(-12).
_mm_rcp_ss = FunctionOperator("_mm_rcp_ss", arity = 1,
                              output_precision = ML_SSE_m128_v1float32,
                              require_header = ["xmmintrin.h"])
_mm_rcp_ps = FunctionOperator("_mm_rcp_ps", arity = 1,
                              output_precision = ML_SSE_m128_v4float32,
                              require_header = ["xmmintrin.h"])
_mm256_rcp_ps = FunctionOperator("_mm256_rcp_ps", arity = 1,
                                 output_precision = ML_AVX_m256_v8float32,
                                 require_header = ["immintrin.h"])

_mm_add_ss = FunctionOperator("_mm_add_ss", arity = 2,
                              output_precision = ML_SSE_m128_v1float32,
                              require_header = ["xmmintrin.h"])
_mm_mul_ss = FunctionOperator("_mm_mul_ss", arity = 2,
                              output_precision = ML_SSE_m128_v4float32,
                              require_header = ["xmmintrin.h"])
_lzcnt_u32 = FunctionOperator("_lzcnt_u32", arity = 1,
        output_precision = ML_UInt32,
        require_header = ["lzcntintrin.h"])
_lzcnt_u64 = FunctionOperator("_lzcnt_u64", arity = 1,
        output_precision = ML_UInt64,
        require_header = ["lzcntintrin.h"])

_mm_cvtss_f32 = FunctionOperator("_mm_cvtss_f32", arity = 1,
                                 output_precision = ML_Binary32,
                                 require_header = ["xmmintrin.h"])

def x86_fma_intrinsic_builder(intr_name):
    return _mm_cvtss_f32(
            FunctionOperator(intr_name, arity = 3,
                             output_precision = ML_SSE_m128_v1float32,
                             require_header = ["immintrin.h"]
                             )(_mm_set_ss(FO_Arg(0)),
                               _mm_set_ss(FO_Arg(1)),
                               _mm_set_ss(FO_Arg(2))))
def x86_fmad_intrinsic_builder(intr_name):
    return _mm_cvtsd_f64(FunctionOperator(intr_name, arity = 3, output_precision = ML_SSE_m128_v1float64, require_header = ["immintrin.h"])(_mm_set_sd(FO_Arg(0)), _mm_set_sd(FO_Arg(1)), _mm_set_sd(FO_Arg(2))))

## Builder for x86 FMA intrinsic within XMM register
# (native, no conversions)
#
def x86_fma_intr_builder_native(intr_name, output_precision = ML_SSE_m128_v1float32):
    return FunctionOperator(intr_name, arity = 3,
                             output_precision = output_precision,
                             require_header = ["immintrin.h"]
                             )
def x86_fmad_intr_builder_native(intr_name, output_precision = ML_SSE_m128_v1float64):
    return FunctionOperator(intr_name, arity = 3,
                            output_precision = output_precision,
                            require_header = ["immintrin.h"]
                            )

## Convert a v4 to m128 conversion optree
def v4_to_m128_modifier(optree):
  conv_input = optree.get_input(0)
  elt_precision = conv_input.get_precision().get_scalar_format()

  elts = [VectorElementSelection(
    conv_input,
    Constant(i, precision = ML_Integer),
    precision = elt_precision
  ) for i in xrange(4)]
  return Conversion(elts[0], elts[1], elts[2], elts[3], precision = optree.get_precision())
__m128ip_cast_operator = TemplateOperatorFormat(
    "(__m128i*){}", arity = 1, 
    output_precision = ML_Pointer_Format(ML_SSE_m128_v4int32)
)

_mm_fmadd_ss = x86_fma_intrinsic_builder("_mm_fmadd_ss")

sse_c_code_generation_table = {
    Conversion: {
      None: {
        lambda _: True: {
          type_strict_match(ML_SSE_m128_v1int32, ML_Int32): _mm_set1_epi32,

          type_strict_match(ML_SSE_m128_v1float32, ML_Binary32): _mm_set_ss,
          type_strict_match(ML_Binary32, ML_SSE_m128_v1float32): _mm_cvtss_f32,

          type_strict_match(ML_SSE_m128_v1float64, ML_Binary64): _mm_set_sd,
          type_strict_match(ML_Binary64, ML_SSE_m128_v1float64): _mm_cvtsd_f64,

          type_strict_match(ML_SSE_m128_v4float32, v4float32):
            XmmIntrin("_mm_load_ps", arity = 1, output_precision = ML_SSE_m128_v4float32)
              #(TemplateOperatorFormat("(__m128*){}", arity = 1, output_precision = ML_Pointer_Format(ML_SSE_m128_v4float32))
                (TemplateOperatorFormat("GET_VEC_FIELD_ADDR({})", arity = 1, output_precision = ML_Pointer_Format(ML_Binary32))),#),
          # m128 float vector to ML's generic vector format
          type_strict_match(v4float32, ML_SSE_m128_v4float32):
            TemplateOperatorFormat("_mm_store_ps(GET_VEC_FIELD_ADDR({}), {})",
              arity = 1,
              arg_map = {0: FO_Result(0), 1: FO_Arg(0)},
              require_header = ["xmmintrin.h"]
            ),
            #XmmIntrin("_mm_store_ps", arity = 2, arg_map = {0: FO_Result(0), 1: FO_Arg(0)})
            #  (FunctionOperator("GET_VEC_FIELD_ADDR", arity = 1, output_precision = ML_Pointer_Format(ML_Binary32))(FO_Result(0)), FO_Arg(0)),

          type_strict_match(v4int32, ML_SSE_m128_v4int32): 
            TemplateOperatorFormat("_mm_store_si128((__m128i*){0}, {1})", arg_map = {0: FO_ResultRef(0), 1: FO_Arg(0)}, void_function = True),

          type_strict_match(ML_SSE_m128_v4int32, ML_Int32, ML_Int32, ML_Int32, ML_Int32): XmmIntrin("_mm_set_epi32", arity = 4),
          #type_strict_match(ML_SSE_m128_v4int32, v4int32): ComplexOperator(optree_modifier = v4_to_m128_modifier),
          type_strict_match(ML_SSE_m128_v4int32, v4int32):
            XmmIntrin("_mm_load_si128", arity = 1, output_precision = ML_SSE_m128_v4int32)
              (__m128ip_cast_operator
                (TemplateOperatorFormat("GET_VEC_FIELD_ADDR({})", arity = 1, output_precision = ML_Pointer_Format(ML_Int32)))),
        }
      },
    },
    BitLogicAnd: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4float32, ML_SSE_m128_v4float32): XmmIntrin("_mm_and_ps", arity = 2, output_precision = ML_SSE_m128_v4float32),
        },
      },
    },
    BitLogicOr: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4float32, ML_SSE_m128_v4float32): XmmIntrin("_mm_or_ps", arity = 2, output_precision = ML_SSE_m128_v4float32),
        },
      },
    },
    # Arithmetic
    Addition: {
        None: {
            lambda _: True: {
                type_strict_match(ML_SSE_m128_v1float32, ML_SSE_m128_v1float32, ML_SSE_m128_v1float32):
                    _mm_add_ss(FO_Arg(0), FO_Arg(1)),
                type_strict_match(ML_Binary32, ML_Binary32, ML_Binary32):
                    _mm_cvtss_f32(_mm_add_ss(_mm_set_ss(FO_Arg(0)),
                                             _mm_set_ss(FO_Arg(1)))),
                # vector addition
                type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4float32, ML_SSE_m128_v4float32): XmmIntrin("_mm_add_ps", arity = 2),
            },
        },
    },
    Subtraction: {
        None: {
            lambda _: True: {
                # vector addition
                type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4float32, ML_SSE_m128_v4float32): XmmIntrin("_mm_sub_ps", arity = 2),
                type_strict_match(ML_SSE_m128_v1float32, ML_SSE_m128_v1float32, ML_SSE_m128_v1float32): XmmIntrin("_mm_sub_ss", arity = 2),
            },
        },
    },
    Multiplication: {
        None: {
            lambda _: True: {
                type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4float32, ML_SSE_m128_v4float32):
                    XmmIntrin("_mm_mul_ps", arity = 2, output_precision = ML_SSE_m128_v4float32),
                type_strict_match(ML_SSE_m128_v1float32, ML_SSE_m128_v1float32, ML_SSE_m128_v1float32):
                    _mm_mul_ss(FO_Arg(0), FO_Arg(1)),
                type_strict_match(ML_Binary32, ML_Binary32, ML_Binary32):
                    _mm_cvtss_f32(_mm_mul_ss(_mm_set_ss(FO_Arg(0)),
                                             _mm_set_ss(FO_Arg(1)))),
                # vector multiplication
                type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4float32, ML_SSE_m128_v4float32): XmmIntrin("_mm_mul_ps", arity = 2),
                # type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4int32, ML_SSE_m128_v4int32): XmmIntrin("_mm_mul_epi32", arity = 2),
            },
        },
    },
    FastReciprocal: {
        None: {
            lambda _: True: {
                type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4float32):
                    XmmIntrin("_mm_rcp_ps", arity = 1),
                type_strict_match(ML_SSE_m128_v1float32, ML_SSE_m128_v1float32):
                    _mm_rcp_ss(FO_Arg(0)),
                type_strict_match(ML_Binary32, ML_Binary32):
                    _mm_cvtss_f32(_mm_rcp_ss(_mm_set_ss(FO_Arg(0)))),
            },
        },
    },
    NearestInteger: {
        None: {
            lambda optree: True: {
                # type_strict_match(ML_Binary32, ML_Binary32): _mm_cvtss_f32(_mm_set_ss(FO_Arg(0))),
                type_strict_match(ML_Int32, ML_Binary32):    _mm_cvt_ss2si(_mm_set_ss(FO_Arg(0))),
            },
        },
    },
}

sse2_c_code_generation_table = {
    NearestInteger: {
        None: {
            lambda optree: True: {
                type_strict_match(ML_Int64, ML_Binary64):    _mm_cvtsd_si64(_mm_set_sd(FO_Arg(0))),
                type_strict_match(ML_Int32, ML_Binary64):    _mm_cvtsd_si32(_mm_set_sd(FO_Arg(0))),
            },
        },
    },
    TypeCast: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4int32): EmmIntrin("_mm_castsi128_ps", arity = 1, output_precision = ML_SSE_m128_v4float32),
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4float32): EmmIntrin("_mm_castps_si128", arity = 1, output_precision = ML_SSE_m128_v4int32),
        },
      },
    },
    Addition: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4int32, ML_SSE_m128_v4int32): EmmIntrin("_mm_add_epi32", arity = 2),
        },
      },
    },
    Subtraction: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4int32, ML_SSE_m128_v4int32): EmmIntrin("_mm_sub_epi32", arity = 2),
        },
      },
    },
    BitLogicAnd: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4int32, ML_SSE_m128_v4int32): EmmIntrin("_mm_and_si128", arity = 2),
        },
      },
    },
    BitLogicOr: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4int32, ML_SSE_m128_v4int32): EmmIntrin("_mm_or_si128", arity = 2),
        },
      },
    },
    BitLogicNegate: {
      None: {
        lambda _: True: {
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4int32):
          ImmIntrin("_mm_andnot_si128", arity = 2)(
              FO_Arg(0),
              FO_Value("_mm_set1_epi32(-1)", ML_SSE_m128_v4int32)
              ),
        },
      },
    },
    BitLogicLeftShift: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4int32, ML_Int32):
            EmmIntrin("_mm_slli_epi32", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)})(FO_Arg(0), _mm_set1_epi64x(FO_Arg(1))),
        },
      },
    },
    BitLogicRightShift: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4int32, ML_Int32):
            EmmIntrin("_mm_srli_epi32", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)})(FO_Arg(0), _mm_set1_epi64x(FO_Arg(1))),
        },
      },
    },
    BitArithmeticRightShift: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4int32, ML_Int32):
            EmmIntrin("_mm_srai_epi32", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)})(FO_Arg(0), _mm_set1_epi64x(FO_Arg(1))),
        },
      },
    },
    Conversion: {
      None: {
        lambda optree: True: {
          type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4int32):
            EmmIntrin("_mm_cvtepi32_ps", arity = 1),
          type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4float32):
            EmmIntrin("_mm_cvtps_epi32", arity = 1),
        },
      },
    },
    Negation: {
        None: {
            lambda optree: True: {
                # Float negation
                type_strict_match(*(2*(ML_SSE_m128_v4float32,))):
                    EmmIntrin("_mm_xor_ps", arity = 2)(
                        FO_Arg(0),
                        FO_Value("_mm_set1_ps(-0.0f)", ML_SSE_m128_v4float32)
                    ),
                type_strict_match(*(2*(ML_SSE_m128_v2float64,))):
                    EmmIntrin("_mm_xor_pd", arity = 2)(
                        FO_Value("_mm_set1_pd(-0.0f)", ML_SSE_m128_v2float64),
                        FO_Arg(0)
                    ),
                # Integer negation
                type_strict_match(*(2*(ML_SSE_m128_v4int32,))):
                    EmmIntrin("_mm_sub_epi32", arity = 2)(
                        FO_Value("_mm_set1_epi32(0)", ML_SSE_m128_v4int32),
                        FO_Arg(0)
                    ),
                type_strict_match(*(2*(ML_SSE_m128_v2int64,))):
                    EmmIntrin("_mm_sub_epi64", arity = 2)(
                        FO_Value("_mm_set1_epi64(0)", ML_SSE_m128_v2int64),
                        FO_Arg(0)
                    ),
            },
        },
    },
}

ssse3_c_code_generation_table = {
    Negation: {
        None: {
            lambda optree: True: {
                # Float negation is handled by SSE2 instructions
                # 32-bit integer negation using SSSE3 sign_epi32 instruction
                type_strict_match(*(2*(ML_SSE_m128_v4int32,))):
                    TmmIntrin("_mm_sign_epi32", arity = 2)(
                        FO_Value("_mm_set1_epi32(-1)", ML_SSE_m128_v4int32),
                        FO_Arg(0)
                    ),
            },
        },
    },
}

sse41_c_code_generation_table = {
    NearestInteger: {
        None: {
            lambda optree: True: {
                type_strict_match(ML_SSE_m128_v1float32, ML_SSE_m128_v1float32): _mm_round_ss_rn,
                type_strict_match(ML_SSE_m128_v1float64, ML_SSE_m128_v1float64): _mm_round_sd_rn,

                type_strict_match(ML_Binary32, ML_Binary32): _mm_cvtss_f32(_mm_round_ss_rn(_mm_set_ss(FO_Arg(0)))),
                type_strict_match(ML_Binary64, ML_Binary64): _mm_cvtsd_f64(_mm_round_sd_rn(_mm_set_sd(FO_Arg(0)))),

                type_strict_match(ML_SSE_m128_v4float32, ML_SSE_m128_v4float32):
                  SmmIntrin("_mm_round_ps", arity = 1, arg_map = {0: FO_Arg(0), 1: "_MM_FROUND_TO_NEAREST_INT"}, output_precision = ML_SSE_m128_v4float32),
                type_strict_match(ML_SSE_m128_v4int32, ML_SSE_m128_v4float32):
                  EmmIntrin("_mm_cvtps_epi32", arity = 1, output_precision = ML_SSE_m128_v4int32)
                    (SmmIntrin("_mm_round_ps", arity = 1, arg_map = {0: FO_Arg(0), 1: "_MM_FROUND_TO_NEAREST_INT"}, output_precision = ML_SSE_m128_v4float32)),
            },
        },
    },
}

#rdtsc_operator = AsmInlineOperator(
#  "__asm volatile ( \"xor %%%%eax, %%%%eax\\n\"\n \"CPUID\\n\" \n\"rdtsc\\n\"\n : \"=A\"(%s));",
#  arg_map = {0: FO_Result(0)},
#  arity = 0
#)

rdtsc_operator = AsmInlineOperator(
"""{
    uint32_t cycles_hi = 0, cycles_lo = 0;
    asm volatile (
  "cpuid\\n\\t"
   "rdtsc\\n\\t"
   "mov %%%%edx, %%0\\n\\t"
   "mov %%%%eax, %%1\\n\\t"
   : "=r" (cycles_hi), "=r" (cycles_lo)
   :: "%%rax", "%%rbx", "%%rcx", "%%rdx");
   %s = ((uint64_t) cycles_hi << 32) | cycles_lo;
   }""",
  arg_map = {0: FO_Result(0)},
  arity = 0
)

x86_c_code_generation_table = {
  SpecificOperation: {
    SpecificOperation.ReadTimeStamp: {
      lambda _: True: {
        type_strict_match(ML_Int64): rdtsc_operator
      }
    }
  },
}

class X86_Processor(VectorBackend):
  target_name = "x86"
  TargetRegister.register_new_target(target_name, lambda _: X86_Processor)

  code_generation_table = {
    C_Code: x86_c_code_generation_table,
  }

  def __init__(self):
    GenericProcessor.__init__(self)

  def get_current_timestamp(self):
    return SpecificOperation(
      specifier = SpecificOperation.ReadTimeStamp,
      precision = ML_Int64
    )


class X86_SSE_Processor(X86_Processor):
    target_name = "x86_sse"
    TargetRegister.register_new_target(target_name, lambda _: X86_SSE_Processor)

    code_generation_table = {
        C_Code: sse_c_code_generation_table,
    }

    def __init__(self):
        GenericProcessor.__init__(self)

class X86_SSE2_Processor(X86_SSE_Processor):
    target_name = "x86_sse2"
    TargetRegister.register_new_target(target_name, lambda _: X86_SSE2_Processor)

    code_generation_table = {
        C_Code: sse2_c_code_generation_table,
    }

    def __init__(self):
        X86_SSE_Processor.__init__(self)

class X86_SSSE3_Processor(X86_SSE2_Processor):
    target_name = "x86_ssse3"
    TargetRegister.register_new_target(target_name, lambda _: X86_SSSE3_Processor)

    code_generation_table = {
        C_Code: ssse3_c_code_generation_table,
    }

    def __init__(self):
        X86_SSE_Processor.__init__(self)

    def get_compilation_options(self):
      return super(X86_SSSE3_Processor, self).get_compilation_options() + ["-mssse3"]

class X86_SSE41_Processor(X86_SSSE3_Processor):
    target_name = "x86_sse41"
    TargetRegister.register_new_target(target_name, lambda _: X86_SSE41_Processor)

    code_generation_table = {
        C_Code: sse41_c_code_generation_table,
    }

    def __init__(self):
        X86_SSE2_Processor.__init__(self)

class X86_AVX2_Processor(X86_SSE41_Processor):
    target_name = "x86_avx2"
    TargetRegister.register_new_target(target_name, lambda _: X86_AVX2_Processor)

    code_generation_table = {
        C_Code: {
            TableLoad: {
              None: {
                lambda optree: True: {
                  # XMM version
                  type_custom_match(FSM(ML_SSE_m128_v4float32), TCM(ML_TableFormat), FSM(ML_SSE_m128_v4int32)): ImmIntrin("_mm_i32gather_ps", arity = 3, output_precision = ML_SSE_m128_v4float32)(FO_Arg(0), FO_Arg(1), FO_Value("4", ML_Int32)),
                  type_custom_match(FSM(ML_SSE_m128_v2float64), TCM(ML_TableFormat), FSM(ML_SSE_m128_v2float64)): ImmIntrin("_mm_i32gather_pd", arity = 3, output_precision = ML_SSE_m128_v4float32)(FO_Arg(0), FO_Arg(1), FO_Value("8", ML_Int32)),
                  # YMM version
                  type_custom_match(FSM(ML_AVX_m256_v8float32), TCM(ML_TableFormat), FSM(ML_AVX_m256_v8float32)): ImmIntrin("_mm256_i32gather_ps", arity = 3, output_precision = ML_AVX_m256_v8float32)(FO_Arg(0), FO_Arg(1), FO_Value("4", ML_Int32)),
                  type_custom_match(FSM(ML_AVX_m256_v4float64), TCM(ML_TableFormat), FSM(ML_AVX_m256_v4float64)): ImmIntrin("_mm256_i32gather_pd", arity = 3, output_precision = ML_AVX_m256_v4float64)(FO_Arg(0), FO_Arg(1), FO_Value("8", ML_Int32)),
                },
              },
            },
            FusedMultiplyAdd: {
              FusedMultiplyAdd.Standard: {
                lambda optree: True: {
                  # Scalar version
                  type_strict_match(*(4*(ML_SSE_m128_v1float32,))): x86_fma_intr_builder_native("_mm_fmadd_ss"),
                  type_strict_match(*(4*(ML_SSE_m128_v1float64,))): x86_fmad_intr_builder_native("_mm_fmadd_sd"),
                  # XMM version
                  type_strict_match(*(4*(ML_SSE_m128_v4float32,))): x86_fma_intr_builder_native("_mm_fmadd_ps", output_precision = ML_SSE_m128_v4float32),
                  type_strict_match(*(4*(ML_SSE_m128_v2float64,))): x86_fmad_intr_builder_native("_mm_fmadd_ps", output_precision = ML_SSE_m128_v2float64),
                  # YMM version
                  type_strict_match(*(4*(ML_AVX_m256_v8float32,))): x86_fma_intr_builder_native("_mm256_fmadd_ps", output_precision = ML_AVX_m256_v8float32),
                  type_strict_match(*(4*(ML_AVX_m256_v4float64,))): x86_fma_intr_builder_native("_mm256_fmadd_pd", output_precision = ML_AVX_m256_v4float64),
                },
              },
              FusedMultiplyAdd.Subtract: {
                lambda optree: True: {
                  # Scalar version
                  type_strict_match(*(4*(ML_SSE_m128_v1float32,))): x86_fma_intr_builder_native("_mm_fmsub_ss"),
                  type_strict_match(*(4*(ML_SSE_m128_v1float64,))): x86_fmad_intr_builder_native("_mm_fmsub_sd"),
                  # XMM version
                  type_strict_match(*(4*(ML_SSE_m128_v4float32,))): x86_fma_intr_builder_native("_mm_fmsub_ps", output_precision = ML_SSE_m128_v4float32),
                  type_strict_match(*(4*(ML_SSE_m128_v2float64,))): x86_fmad_intr_builder_native("_mm_fmsub_ps", output_precision = ML_SSE_m128_v2float64),
                  # YMM version
                  type_strict_match(*(4*(ML_AVX_m256_v8float32,))): x86_fma_intr_builder_native("_mm256_fmsub_ps", output_precision = ML_AVX_m256_v8float32),
                  type_strict_match(*(4*(ML_AVX_m256_v4float64,))): x86_fma_intr_builder_native("_mm256_fmsub_pd", output_precision = ML_AVX_m256_v4float64),
                },
              },
              FusedMultiplyAdd.SubtractNegate: {
                lambda optree: True: {
                  # Scalar version
                  type_strict_match(*(4*(ML_SSE_m128_v1float32,))): x86_fma_intr_builder_native("_mm_fnmadd_ss"),
                  type_strict_match(*(4*(ML_SSE_m128_v1float64,))): x86_fmad_intr_builder_native("_mm_fnmadd_sd"),
                  # XMM version
                  type_strict_match(*(4*(ML_SSE_m128_v4float32,))): x86_fma_intr_builder_native("_mm_fnmadd_ps", output_precision = ML_SSE_m128_v4float32),
                  type_strict_match(*(4*(ML_SSE_m128_v2float64,))): x86_fmad_intr_builder_native("_mm_fnmadd_ps", output_precision = ML_SSE_m128_v2float64),
                  # YMM version
                  type_strict_match(*(4*(ML_AVX_m256_v8float32,))): x86_fma_intr_builder_native("_mm256_fnmadd_ps", output_precision = ML_AVX_m256_v8float32),
                  type_strict_match(*(4*(ML_AVX_m256_v4float64,))): x86_fma_intr_builder_native("_mm256_fnmadd_pd", output_precision = ML_AVX_m256_v4float64),
                },
              },
              FusedMultiplyAdd.Negate: {
                lambda optree: True: {
                  # Scalar version
                  type_strict_match(*(4*(ML_SSE_m128_v1float32,))): x86_fma_intr_builder_native("_mm_fnmsub_ss"),
                  type_strict_match(*(4*(ML_SSE_m128_v1float64,))): x86_fmad_intr_builder_native("_mm_fnmsub_sd"),
                  # XMM version
                  type_strict_match(*(4*(ML_SSE_m128_v4float32,))): x86_fma_intr_builder_native("_mm_fnmsub_ps", output_precision = ML_SSE_m128_v4float32),
                  type_strict_match(*(4*(ML_SSE_m128_v2float64,))): x86_fmad_intr_builder_native("_mm_fnmsub_ps", output_precision = ML_SSE_m128_v2float64),
                  # YMM version
                  type_strict_match(*(4*(ML_AVX_m256_v8float32,))): x86_fma_intr_builder_native("_mm256_fnmsub_ps", output_precision = ML_AVX_m256_v8float32),
                  type_strict_match(*(4*(ML_AVX_m256_v4float64,))): x86_fma_intr_builder_native("_mm256_fnmsub_pd", output_precision = ML_AVX_m256_v4float64),
                },
              },
            },
            CountLeadingZeros: {
                None: {
                    lambda _: True: {
                        #type_strict_match(ML_UInt32, ML_UInt32):
                        #_lzcnt_u32(FO_Arg(0)),
                        #type_strict_match(ML_UInt64, ML_UInt64):
                        #_lzcnt_u64(FO_Arg(0)),
                    },
                },
            },
            BitLogicLeftShift: {
                None: {
                  lambda _: True: {
                    # TODO implement fixed bit shift (sll, slli)
                    # Variable bit shift is only available with AVX2
                    # XMM version
                    type_strict_match(*(3*(ML_SSE_m128_v4int32,))): ImmIntrin("_mm_sllv_epi32", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                    type_strict_match(*(3*(ML_SSE_m128_v2int64,))): ImmIntrin("_mm_sllv_epi64", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                    # YMM version
                    type_strict_match(*(3*(ML_AVX_m256_v8int32,))): ImmIntrin("_mm256_sllv_epi32", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                    type_strict_match(*(3*(ML_AVX_m256_v4int64,))): ImmIntrin("_mm256_sllv_epi64", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                  },
              },
            },
            BitLogicRightShift: {
                None: {
                  lambda optree: True: {
                    # XMM version
                    type_strict_match(*(3*(ML_SSE_m128_v4int32,))): ImmIntrin("_mm_srlv_epi32", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                    type_strict_match(*(3*(ML_SSE_m128_v2int64,))): ImmIntrin("_mm_srlv_epi64", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                    # YMM version
                    type_strict_match(*(3*(ML_AVX_m256_v8int32,))): ImmIntrin("_mm256_srlv_epi32", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                    type_strict_match(*(3*(ML_AVX_m256_v4int64,))): ImmIntrin("_mm256_srlv_epi64", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                  },
              },
            },
            BitArithmeticRightShift: {
                None: {
                  lambda _: True: {
                    # XMM version
                    type_strict_match(*(3*(ML_SSE_m128_v4int32,))): ImmIntrin("_mm_srav_epi32", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                    type_strict_match(*(3*(ML_SSE_m128_v2int64,))): ImmIntrin("_mm_srav_epi64", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                    # YMM version
                    type_strict_match(*(3*(ML_AVX_m256_v8int32,))): ImmIntrin("_mm256_srav_epi32", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                    type_strict_match(*(3*(ML_AVX_m256_v4int64,))): ImmIntrin("_mm256_srav_epi64", arity = 2, arg_map = {0: FO_Arg(0), 1: FO_Arg(1)}),
                  },
                },
            },
        },
    }

    def __init__(self):
        X86_SSE41_Processor.__init__(self)

    def get_compilation_options(self):
      return super(X86_AVX2_Processor, self).get_compilation_options() + ["-mfma", "-mavx2"]


# debug message
print "initializing INTEL targets"
