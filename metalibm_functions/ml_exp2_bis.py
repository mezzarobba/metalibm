# -*- coding: utf-8 -*-

import sys

import sollya

from sollya import S2, Interval, ceil, floor, round, inf, sup, log, exp, expm1, log2, guessdegree, dirtyinfnorm, RN

from metalibm_core.core.attributes import ML_Debug
from metalibm_core.core.ml_operations import *
from metalibm_core.core.ml_formats import *
from metalibm_core.core.ml_table import ML_NewTable
from metalibm_core.code_generation.generic_processor import GenericProcessor
from metalibm_core.core.polynomials import *
from metalibm_core.core.ml_function import ML_Function, ML_FunctionBasis, DefaultArgTemplate
from metalibm_core.code_generation.generator_utility import FunctionOperator, FO_Result, FO_Arg
from metalibm_core.core.ml_complex_formats import ML_Mpfr_t


from metalibm_core.utility.ml_template import *
from metalibm_core.utility.log_report  import Log
from metalibm_core.utility.debug_utils import *
from metalibm_core.utility.num_utils   import ulp
from metalibm_core.utility.gappa_utils import is_gappa_installed



class ML_Exp2(ML_Function("ml_exp2")):
  def __init__(self,
             arg_template = DefaultArgTemplate,
             precision = ML_Binary32,
             accuracy  = ML_Faithful,
             libm_compliant = True,
             debug_flag = False,
             fuse_fma = True,
             fast_path_extract = True,
             target = GenericProcessor(),
             output_file = "my_exp2.c",
             function_name = "my_exp2",
             language = C_Code,
             vector_size = 1):
    # initializing I/O precision
    precision = ArgDefault.select_value([arg_template.precision, precision])
    io_precisions = [precision] * 2

    # initializing base class
    ML_FunctionBasis.__init__(self,
      base_name = "exp2",
      function_name = function_name,
      output_file = output_file,

      io_precisions = io_precisions,
      abs_accuracy = None,
      libm_compliant = libm_compliant,

      processor = target,
      fuse_fma = fuse_fma,
      fast_path_extract = fast_path_extract,

      debug_flag = debug_flag,
      language = language,
      vector_size = vector_size,
      arg_template = arg_template
    )

    self.accuracy  = accuracy
    self.precision = precision

  def generate_scheme(self):
    # declaring target and instantiating optimization engine

    vx = self.implementation.add_input_variable("x", self.precision)

    Log.set_dump_stdout(True)

    Log.report(Log.Info, "\033[33;1m generating implementation scheme \033[0m")
    if self.debug_flag:
        Log.report(Log.Info, "\033[31;1m debug has been enabled \033[0;m")

    # local overloading of RaiseReturn operation
    def ExpRaiseReturn(*args, **kwords):
        kwords["arg_value"] = vx
        kwords["function_name"] = self.function_name
        return RaiseReturn(*args, **kwords)

    r_interval = Interval(-1.0, 1.0)

    local_ulp = sup(ulp(2**r_interval, self.precision))
    print "ulp: ", local_ulp
    error_goal = S2**-1*local_ulp
    print "error goal: ", error_goal

    sollya_prec_map = {ML_Binary32: sollya.binary32, ML_Binary64: sollya.binary64}
    int_prec_map = {ML_Binary32: ML_Int32, ML_Binary64: ML_Int64}

    #Argument Reduction
    vx_int = Trunc(vx, precision = self.precision, tag = 'vx_int', debug = debug_multi)
    ivx = Conversion(vx_int, precision = int_prec_map[self.precision])
    vx_r = vx - vx_int
    vx_r.set_attributes(tag = "vx_r", debug = debug_multi)
    degree = sup(guessdegree(2**(sollya.x), r_interval, error_goal)) + 2
    precision_list = [1] + [self.precision] * degree


    exp_X = ExponentInsertion(ivx, tag = "exp_X", debug = debug_multi, precision = self.precision)

    #Polynomial Approx
    polynomial_scheme_builder = PolynomialSchemeEvaluator.generate_horner_scheme

    poly_object, poly_error = Polynomial.build_from_approximation_with_error(2**(sollya.x), degree, precision_list, r_interval, sollya.absolute)
    Log.report(Log.Info, "Poly : %s" % poly_object)
    print "poly_error : ", poly_error
    poly = polynomial_scheme_builder(poly_object, vx_r, unified_precision = self.precision)
    poly.set_attributes(tag = "poly", debug = debug_multi)



    #Handling special cases
    oflow_bound = self.precision.get_emax()
    subnormal_bound = self.precision.get_emin_subnormal()
    uflow_bound = self.precision.get_emin_normal()
    #print "oflow : ", oflow_bound
    #print "uflow : ", uflow_bound
    #print "sub : ", subnormal_bound
    test_overflow = Comparison(vx_int, oflow_bound, specifier = Comparison.Greater)
    test_overflow.set_attributes(tag = "oflow_test", debug = debug_multi)

    test_underflow = Comparison(vx_int, uflow_bound, specifier = Comparison.Less)
    test_underflow.set_attributes(tag = "uflow_test", debug = debug_multi)

    test_subnormal = Comparison(vx_int, subnormal_bound, specifier = Comparison.Greater)
    test_subnormal.set_attributes(tag = "sub_test", debug = debug_multi)

    subnormal_offset = - (uflow_bound - ivx)
    subnormal_offset.set_attributes( tag = "offset", debug = debug_multi)
    exp_offset = ExponentInsertion(subnormal_offset, precision = self.precision, debug = debug_multi, tag = "exp_offset")
    exp_min = ExponentInsertion(uflow_bound, precision = self.precision, debug = debug_multi, tag = "exp_min")
    subnormal_result = exp_offset*exp_min*poly

    #Reconstruction
    result = exp_X*poly
    result.set_attributes(tag = "result", debug = debug_multi)

    scheme = Statement(
        ConditionBlock(
            test_overflow,
            Return(FP_PlusInfty(self.precision)),
            ConditionBlock(
                test_underflow,
                ConditionBlock(
                    test_subnormal,
                    Return(subnormal_result),
                    Return(0)
                    ),
                Return(result)
            )))

    return scheme

  def generate_emulate(self, result_ternary, result, mpfr_x, mpfr_rnd):
    """ generate the emulation code for ML_Log2 functions
        mpfr_x is a mpfr_t variable which should have the right precision
        mpfr_rnd is the rounding mode
    """
    emulate_func_name = "mpfr_exp"
    emulate_func_op = FunctionOperator(emulate_func_name, arg_map = {0: FO_Arg(0), 1: FO_Arg(1), 2: FO_Arg(2)}, require_header = ["mpfr.h"])
    emulate_func   = FunctionObject(emulate_func_name, [ML_Mpfr_t, ML_Mpfr_t, ML_Int32], ML_Int32, emulate_func_op)
    mpfr_call = Statement(ReferenceAssign(result_ternary, emulate_func(result, mpfr_x, mpfr_rnd)))

    return mpfr_call

  def numeric_emulate(self, input_value):
    return sollya.SollyaObject(2)**(input_value)

  standard_test_cases = [(sollya.parse("-0x1.6775b4p+6"),)]

if __name__ == "__main__":
    # auto-test
    arg_template = ML_NewArgTemplate(default_function_name = "new_exp2", default_output_file = "new_exp2.c" )
    # argument extraction
    args = parse_arg_index_list = arg_template.arg_extraction()

    ml_exp2          = ML_Exp2(args)

    ml_exp2.gen_implementation()