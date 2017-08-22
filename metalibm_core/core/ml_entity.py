# -*- coding: utf-8 -*-

###############################################################################
# This file is part of New Metalibm tool
# Copyright (2016-)
# All rights reserved
# created:          Nov 17th, 2016    
# last-modified:    May  9th, 2017
#
# author(s):   Nicolas Brunie (nibrunie@gmail.com)
# decription:  Declare and implement a class to manage
#              hardware (vhdl like) entities
###############################################################################

from sollya import *

from metalibm_core.core.ml_formats import *
from metalibm_core.core.ml_optimization_engine import OptimizationEngine
from metalibm_core.core.ml_operations import *  
from metalibm_core.core.ml_hdl_operations import *  
from metalibm_core.core.ml_table import ML_Table
from metalibm_core.core.ml_complex_formats import ML_Mpfr_t
from metalibm_core.core.ml_call_externalizer import CallExternalizer
from metalibm_core.core.ml_vectorizer import StaticVectorizer

from metalibm_core.core.precisions import ML_Faithful

from metalibm_core.code_generation.code_object import NestedCode, VHDLCodeObject, CodeObject
from metalibm_core.code_generation.code_entity import CodeEntity
from metalibm_core.code_generation.vhdl_backend import VHDLBackend
from metalibm_core.code_generation.vhdl_code_generator import VHDLCodeGenerator
from metalibm_core.code_generation.code_constant import VHDL_Code
from metalibm_core.code_generation.generator_utility import *

from metalibm_core.core.passes import *

from metalibm_core.code_generation.gappa_code_generator import GappaCodeGenerator

from metalibm_core.utility.log_report import Log
from metalibm_core.utility.debug_utils import *
from metalibm_core.utility.ml_template import ArgDefault, DefaultEntityArgTemplate

import random
import subprocess

def generate_random_fp_value(precision, inf, sup):
    """ Generate a random floating-point value of format precision """
    assert isinstance(precision, ML_FP_Format)
    value = random.uniform(0.5, 1.0) * S2**random.randrange(precision.get_emin_normal(), 1) * (sup - inf) + inf
    rounded_value = precision.round_sollya_object(value, RN)
    return rounded_value

def generate_random_fixed_value(precision):
    """ Generate a random fixed-point value of format precision """
    assert is_fixed_point(precision)
    # fixed point format
    lo_value = precision.get_min_value()
    hi_value = precision.get_max_value()
    value = random.uniform(
      lo_value,
      hi_value 
    )
    rounded_value = input_precision.round_sollya_object(value)
    return rounded_value

## \defgroup ml_entity ml_entity
## @{


# return a random value in the given @p interval
# Samplin is done uniformly on value exponent, 
# not on the value itself
def random_log_sample(interval):
  lo = inf(interval)
  hi = sup(interval)


debug_utils_lib = """proc get_fixed_value {value weight} {
  return [expr $value * pow(2.0, $weight)]
}\n"""
  
class RetimeMap:
  def __init__(self):
    # map (op_key, stage) -> stage's op
    self.stage_map = {}
    # map of stage_index -> list of pipelined forward 
    # from <stage_index> -> <stage_index + 1>
    self.stage_forward = {}
    # list of nodes already retimed
    self.processed = []
    # 
    self.pre_statement = set()

  def get_op_key(self, op):
    op_key = op.attributes.init_op if not op.attributes.init_op is None else op
    return op_key

  def hasBeenProcessed(self, op):
    return self.get_op_key(op)  in self.processed
  def addToProcessed(self, op):
    op_key = self.get_op_key(op)
    return self.processed.append(op_key)

  def contains(self, op, stage):
    return (self.get_op_key(op), stage) in self.stage_map

  def get(self, op, stage):
    return self.stage_map[(self.get_op_key(op), stage)]
  def set(self, op, stage):
    op_key = self.get_op_key(op)
    self.stage_map[(op_key, stage)] = op

  def add_stage_forward(self, op_dst, op_src, stage):
    Log.report(Log.Verbose, " adding stage forward {op_src} to {op_dst} @ stage {stage}".format(op_src = op_src, op_dst = op_dst, stage = stage))
    if not stage in self.stage_forward:
      self.stage_forward[stage] = []
    self.stage_forward[stage].append(
      ReferenceAssign(op_dst, op_src)
    )
    self.pre_statement.add(op_src)

## Base class for all metalibm function (metafunction)
class ML_EntityBasis(object):
  name = "entity_basis"

  ## constructor
  #  @param base_name string function name (without precision considerations)
  #  @param function_name 
  #  @param output_file string name of source code output file
  #  @param debug_file string name of debug script output file
  #  @param io_precisions input/output ML_Format list
  #  @param abs_accuracy absolute accuracy
  #  @param libm_compliant boolean flag indicating whether or not the function should be compliant with standard libm specification (wrt exception, error ...)
  #  @param fast_path_extract boolean flag indicating whether or not fast path extraction optimization must be applied
  #  @param debug_flag boolean flag, indicating whether or not debug code must be generated 
  def __init__(self,
             # Naming
             base_name = ArgDefault("unknown_entity", 2),
             entity_name= ArgDefault(None, 2),
             output_file = ArgDefault(None, 2),
             # Specification
             io_precisions = ArgDefault([ML_Binary32], 2), 
             abs_accuracy = ArgDefault(None, 2),
             libm_compliant = ArgDefault(True, 2),
             # Optimization parameters
             backend = ArgDefault(VHDLBackend(), 2),
             fast_path_extract = ArgDefault(True, 2),
             # Debug verbosity
             debug_flag = ArgDefault(False, 2),
             language = ArgDefault(VHDL_Code, 2),
             arg_template = DefaultEntityArgTemplate 
         ):
    # selecting argument values among defaults
    base_name = ArgDefault.select_value([base_name])
    print "pre entity_name: ", entity_name, arg_template.entity_name
    entity_name = ArgDefault.select_value([arg_template.entity_name, entity_name])
    print "entity_name: ", entity_name
    print "output_file: ", arg_template.output_file, output_file 
    print "debug_file:  ", arg_template.debug_file
    output_file = ArgDefault.select_value([arg_template.output_file, output_file])
    debug_file  = arg_template.debug_file
    # Specification
    io_precisions = ArgDefault.select_value([io_precisions])
    abs_accuracy = ArgDefault.select_value([abs_accuracy])
    # Optimization parameters
    backend = ArgDefault.select_value([arg_template.backend, backend])
    fast_path_extract = ArgDefault.select_value([arg_template.fast_path_extract, fast_path_extract])
    # Debug verbosity
    debug_flag    = ArgDefault.select_value([arg_template.debug, debug_flag])
    language      = ArgDefault.select_value([arg_template.language, language])
    auto_test     = arg_template.auto_test or arg_template.auto_test_execute
    auto_test_std = arg_template.auto_test_std

    self.precision = arg_template.precision
    self.pipelined = arg_template.pipelined

    # io_precisions must be a list
    #     -> with a single element
    # XOR -> with as many elements as function arity (input + output arities)
    self.io_precisions = io_precisions


    ## enable the generation of numeric/functionnal auto-test
    self.auto_test_enable  = (auto_test != False or auto_test_std != False)
    self.auto_test_number  = auto_test
    self.auto_test_execute = arg_template.auto_test_execute
    self.auto_test_range   = arg_template.auto_test_range
    self.auto_test_std     = auto_test_std 

    # enable/disable automatic exit once functional test is finished
    self.exit_after_test   = arg_template.exit_after_test

    # enable post-generation RTL elaboration
    self.build_enable = arg_template.build_enable

    self.language = language

    # Naming logic, using provided information if available, otherwise deriving from base_name
    # base_name is e.g. exp
    # entity_name is e.g. expf or expd or whatever 
    self.entity_name = entity_name if entity_name else generic_naming(base_name, self.io_precisions)

    self.output_file = output_file if output_file else self.entity_name + ".vhd"
    self.debug_file  = debug_file  if debug_file  else "{}_dbg.do".format(self.entity_name)

    # debug version
    self.debug_flag = debug_flag
    # debug display 
    self.display_after_gen = arg_template.display_after_gen
    self.display_after_opt = arg_template.display_after_opt

    # TODO: FIX which i/o precision to select
    # TODO: incompatible with fixed-point formats
    # self.sollya_precision = self.get_output_precision().get_sollya_object()

    self.abs_accuracy = abs_accuracy if abs_accuracy else S2**(-self.get_output_precision().get_precision())

    # target selection
    self.backend = backend

    # optimization parameters
    self.fast_path_extract = fast_path_extract

    self.implementation = CodeEntity(self.entity_name)

    self.vhdl_code_generator = VHDLCodeGenerator(self.backend, declare_cst = False, disable_debug = not self.debug_flag, language = self.language)
    uniquifier = self.entity_name
    self.main_code_object = NestedCode(self.vhdl_code_generator, static_cst = False, uniquifier = "{0}_".format(self.entity_name), code_ctor = VHDLCodeObject)
    if self.debug_flag:
      self.debug_code_object = CodeObject(self.language)
      self.debug_code_object << debug_utils_lib
      self.vhdl_code_generator.set_debug_code_object(self.debug_code_object)

    # pass scheduler instanciation
    self.pass_scheduler = PassScheduler()
    # recursive pass dependency
    pass_dep = PassDependency()
    for pass_uplet in arg_template.passes:
      pass_slot_tag, pass_tag = pass_uplet.split(":")
      pass_slot = PassScheduler.get_tag_class(pass_slot_tag)
      pass_class  = Pass.get_pass_by_tag(pass_tag)
      pass_object = pass_class(self.backend) 
      self.pass_scheduler.register_pass(pass_object, pass_dep = pass_dep, pass_slot = pass_slot)
      # linearly linking pass in the order they appear
      pass_dep = AfterPassById(pass_object.get_pass_id())

  def get_pass_scheduler(self):
    return self.pass_scheduler


  ## Class method to generate a structure containing default arguments
  #  which must be overloaded by @p kw
  @staticmethod
  def get_default_args(**kw):
    return DefaultEntityArgTemplate(**kw)

  def get_implementation(self):
    return self.implementation

  ## name generation
  #  @param base_name string, name to be extended for unifiquation
  def uniquify_name(self, base_name):
    """ return a unique identifier, combining base_name + function_name """
    return "%s_%s" % (self.function_name, base_name)

  ## emulation code generation
  def generate_emulate(self):
    raise NotImplementedError


  ## propagate forward @p op until it is defined
  #  in @p stage
  def propagate_op(self, op, stage, retime_map):
    op_key = retime_map.get_op_key(op)
    Log.report(Log.Verbose, " propagating {op} (key={op_key}) to stage {stage}".format(op = op, op_key = op_key, stage = stage))
    # look for the latest stage where op is defined
    current_stage = op_key.attributes.init_stage
    while retime_map.contains(op_key, current_stage + 1):
      current_stage += 1
    op_src = retime_map.get(op_key, current_stage)
    while current_stage != stage:  
      # create op instance for <current_stage+1>
      op_dst = Signal(tag = "{tag}_S{stage}".format(
        tag = op_key.get_tag(), stage = (current_stage + 1)),
        init_stage = current_stage + 1, init_op = op_key,
        precision = op_key.get_precision(), var_type = Variable.Local)
      retime_map.add_stage_forward(op_dst, op_src, current_stage)
      retime_map.set(op_dst, current_stage + 1)
      # update values for next iteration
      current_stage += 1
      op_src = op_dst


  # process op's inputs and if necessary
  # propagate them to op's stage
  def retime_op(self, op, retime_map):
    Log.report(Log.Verbose, "retiming op %s " % (op.get_str(depth = 1)))
    if retime_map.hasBeenProcessed(op):
      Log.report(Log.Verbose, "  retiming already processed")
      return
    op_stage = op.attributes.init_stage
    if not isinstance(op, ML_LeafNode):
      for in_id in range(op.get_input_num()):
        in_op = op.get_input(in_id)
        in_stage = in_op.attributes.init_stage
        Log.report(Log.Verbose, "retiming input {inp} of {op} stage {in_stage} -> {op_stage}".format(inp = in_op.get_str(depth = 1), op = op, in_stage = in_stage, op_stage = op_stage))
        if not retime_map.hasBeenProcessed(in_op):
          self.retime_op(in_op, retime_map)
        if in_stage < op_stage:
          if not retime_map.contains(in_op, op_stage):
            self.propagate_op(in_op, op_stage, retime_map)
          new_in = retime_map.get(in_op, op_stage)
          Log.report(Log.Verbose, "new version of input {inp} for {op} is {new_in}".format(inp = in_op, op = op, new_in = new_in))
          op.set_input(in_id, new_in)
        elif in_stage > op_stage:
          Log.report(Log.Error, "input {inp} of {op} is defined at a later stage".format(inp = in_op, op = op))
    retime_map.set(op, op_stage)
    retime_map.addToProcessed(op)
        
  # try to extract 'clk' input or create it if 
  # it does not exist
  def get_clk_input(self):
    clk_in = self.implementation.get_input_by_tag("clk")
    if not clk_in is None:
      return clk_in
    else:
      return self.implementation.add_input_signal('clk', ML_StdLogic)


  def generate_pipeline_stage(self):
    retiming_map = {}
    retime_map = RetimeMap()
    output_assign_list = self.implementation.get_output_assign()
    for output in output_assign_list:
      Log.report(Log.Verbose, "generating pipeline from output %s " % (output.get_str(depth = 1)))
      self.retime_op(output, retime_map)
    process_statement = Statement()

    # adding stage forward process
    clk = self.get_clk_input()
    for stage_id in sorted(retime_map.stage_forward.keys()):
      stage_block = ConditionBlock(
        LogicalAnd(
          Event(clk, precision = ML_Bool),
          Comparison(
            clk,
            Constant(1, precision = ML_StdLogic),
            specifier = Comparison.Equal,
            precision = ML_Bool
          ),
          precision = ML_Bool
        ),
        Statement(*tuple(assign for assign in retime_map.stage_forward[stage_id]))
      )
      process_statement.add(stage_block)
    pipeline_process = Process(process_statement, sensibility_list = [clk])
    for op in retime_map.pre_statement:
      pipeline_process.add_to_pre_statement(op)
    self.implementation.add_process(pipeline_process)
    stage_num = len(retime_map.stage_forward.keys())
    print "there are %d pipeline stages" % (stage_num)
      

  def get_output_precision(self):
    return self.io_precisions[0]

  def get_input_precision(self):
    return self.io_precisions[-1]


  def get_sollya_precision(self):
    """ return the main precision use for sollya calls """
    return self.sollya_precision

  def generate_interfaces(self):
    """ Generate entity interfaces """
    raise NotImplementedError

  def generate_scheme(self):
    """ generate MDL scheme for function implementation """
    Log.report(Log.Error, "generate_scheme must be overloaded by ML_EntityBasis child")

  ## 
  # @return main_scheme, [list of sub-CodeFunction object]
  def generate_entity_list(self):
    return self.generate_scheme()

  ## submit operation node to a standard optimization procedure
  #  @param pre_scheme ML_Operation object to be optimized
  #  @param copy  dict(optree -> optree) copy map to be used while duplicating pre_scheme (if None disable copy)
  #  @param enable_subexpr_sharing boolean flag, enables sub-expression sharing optimization
  #  @param verbose boolean flag, enable verbose mode
  #  @return optimizated scheme 
  def optimise_scheme(self, pre_scheme, copy = None, enable_subexpr_sharing = True, verbose = True):
    """ default scheme optimization """
    # copying when required
    scheme = pre_scheme if copy is None else pre_scheme.copy(copy)
    return scheme


  ## 
  #  @return main code object associted with function implementation
  def get_main_code_object(self):
    return self.main_code_object


  ## generate VHDL code for entity implenetation 
  #  Code is generated within the main code object
  #  and dumped to a file named after implementation's name
  #  @param code_function_list list of CodeFunction to be generated (as sub-function )
  #  @return void
  def generate_code(self, code_entity_list, language = VHDL_Code):
    """ Final VHDL generation, once the evaluation scheme has been optimized"""
    # registering scheme as function implementation
    #self.implementation.set_scheme(scheme)
    # main code object
    code_object = self.get_main_code_object()

    # list of ComponentObject which are entities on which self depends
    common_entity_list = []
    generated_entity = []

    self.result = code_object
    code_str = ""
    while len(code_entity_list) > 0:
      code_entity = code_entity_list.pop(0)
      if code_entity in generated_entity:
        continue
      entity_code_object = NestedCode(self.vhdl_code_generator, static_cst = False, uniquifier = "{0}_".format(self.entity_name), code_ctor = VHDLCodeObject)
      result = code_entity.add_definition(self.vhdl_code_generator, language, entity_code_object, static_cst = False)
      result.add_library("ieee")
      result.add_header("ieee.std_logic_1164.all")
      result.add_header("ieee.std_logic_arith.all")
      result.add_header("ieee.std_logic_misc.all")
      code_str += result.get(self.vhdl_code_generator, headers = True)

      generated_entity.append(code_entity)

      # adding the entities encountered during code generation
      # for future generation
      extra_entity_list = [
            comp_object.get_code_entity() for comp_object in
                entity_code_object.get_entity_list()
      ]
      Log.report(Log.Info, "appending {} extra entit(y/ies)\n".format(len(extra_entity_list)))
      code_entity_list += extra_entity_list

    Log.report(Log.Verbose, "Generating VHDL code in " + self.output_file)
    output_stream = open(self.output_file, "w")
    output_stream.write(code_str)
    output_stream.close()
    if self.debug_flag:
      Log.report(Log.Verbose, "Generating Debug code in {}".format(self.debug_file))
      debug_code_str = self.debug_code_object.get(None)
      debug_stream = open(self.debug_file, "w")
      debug_stream.write(debug_code_str)
      debug_stream.close()


  def gen_implementation(self, 
			display_after_gen = False, 
			display_after_opt = False, 
			enable_subexpr_sharing = True
		):
    # generate scheme
    code_entity_list = self.generate_entity_list()
    
    if self.pipelined:
        self.generate_pipeline_stage()

    if self.auto_test_enable:
      code_entity_list += self.generate_auto_test(
				test_num = self.auto_test_number if self.auto_test_number else 0, 
				test_range = self.auto_test_range
			)
      

    for code_entity in code_entity_list:
      scheme = code_entity.get_scheme()
      if display_after_gen or self.display_after_gen:
        print "function %s, after gen " % code_entity.get_name()
        print scheme.get_str(depth = None, display_precision = True, memoization_map = {})

      # optimize scheme
      opt_scheme = self.optimise_scheme(scheme, enable_subexpr_sharing = enable_subexpr_sharing)

      if display_after_opt or self.display_after_opt:
        print "function %s, after opt " % code_entity.get_name()
        print scheme.get_str(depth = None, display_precision = True, memoization_map = {})

    ## apply @p pass_object optimization pass
    #  to the scheme of each entity in code_entity_list
    def entity_execute_pass(scheduler, pass_object, code_entity_list):
      for code_entity in code_entity_list:
        entity_scheme = code_entity.get_scheme()
        processed_scheme = pass_object.execute(entity_scheme)
        # todo check pass effect
        # code_entity.set_scheme(processed_scheme)
      return code_entity_list
      

    print "Applying passes just before codegen"
    code_entity_list = self.pass_scheduler.get_full_execute_from_slot(
      code_entity_list, 
      PassScheduler.JustBeforeCodeGen,
      entity_execute_pass
    )

    # generate VHDL code to implement scheme
    self.generate_code(code_entity_list, language = self.language)

    if self.auto_test_execute:
      # rtl elaboration
      print "Elaborating {}".format(self.output_file)
      elab_cmd = "vlib work && vcom -2008 {}".format(self.output_file)
      elab_result = subprocess.call(elab_cmd, shell = True)
      print "Elaboration result: ", elab_result
      # debug cmd
      debug_cmd = "do {debug_file};".format(debug_file = self.debug_file) if self.debug_flag else "" 
      debug_cmd += " exit;" if self.exit_after_test else ""
      # simulation
      test_delay = 10 * (self.auto_test_number + (len(self.standard_test_cases) if self.auto_test_std else 0) + 10) 
      sim_cmd = "vsim -c work.testbench -do \"run {test_delay} ns; {debug_cmd}\"".format(entity = self.entity_name, debug_cmd = debug_cmd, test_delay = test_delay)
      sim_result = subprocess.call(sim_cmd, shell = True)
      print "Simulation result: ", sim_result

    elif self.build_enable:
      print "Elaborating {}".format(self.output_file)
      elab_cmd = "vlib work && vcom -2008 {}".format(self.output_file)
      elab_result = subprocess.call(elab_cmd, shell = True)
      print "elab_result: ", elab_result
    

  # Currently mostly empty, to be populated someday
  def gen_emulation_code(self, precode, code, postcode):
    """generate C code that emulates the function, typically using MPFR.
    precode is declaration code (before the test loop)
    postcode is clean-up code (after the test loop)
    Takes the input and output names from input_list and output_list.
    Must postfix output names with "ref_", "ref_ru_", "ref_rd_"

    This class method performs commonly used initializations. 
    It initializes the MPFR versions of the inputs and outputs, 
    with the same names prefixed with "mp" and possibly postfixed with "rd" and "ru".

    It should be overloaded by actual metafunctions, and called by the overloading function. 
    """

  ## provide numeric evaluation of the main function on @p input_value
  def numeric_emulate(self, input_value):
    raise NotImplementedError

  def generate_test_case(self, input_signals, io_map, index, test_range = Interval(-1.0, 1.0)):
    """ generic test case generation: generate a random input
        with index @p index
        
        Args:
            index (int): integer index of the test case
            
        Returns:
            dict: mapping (input tag -> numeric value)
    """
    # extracting test interval boundaries
    low_input = inf(test_range)
    high_input = sup(test_range)
    input_values = {}
    for input_tag in input_signals:
        input_signal = io_map[input_tag]
        # FIXME: correct value generation depending on signal precision
        input_precision = input_signal.get_precision().get_base_format()
        if isinstance(input_precision, ML_FP_Format):
            input_value = generate_random_fp_value(input_precision, low_input, high_input)
        elif isinstance(input_precision, ML_Fixed_Format):
            # TODO: does not depend on low and high range bounds
            input_value = generate_random_fixed_value(input_precision)
        else: 
            input_value = random.randrange(2**input_precision.get_bit_size())
        # registering input value
        input_values[input_tag] = input_value
    return input_values

  def init_test_generator(self):
    """ Generic initialization of test case generator """
    return

  def generate_auto_test(self, test_num = 10, test_range = Interval(-1.0, 1.0), debug = False):
    # instanciating tested component
    # map of input_tag -> input_signal and output_tag -> output_signal
    io_map = {}
    # map of input_tag -> input_signal, excludind commodity signals
    # (e.g. clock and reset)
    input_signals = {}
    # map of output_tag -> output_signal
    output_signals = {}
    # excluding clock and reset signals from argument list
    # reduced_arg_list = [input_port for input_port in self.implementation.get_arg_list() if not input_port.get_tag() in ["clk", "reset"]]
    reduced_arg_list = self.implementation.get_arg_list()
    for input_port in reduced_arg_list:
      input_tag = input_port.get_tag()
      input_signal = Signal(input_tag + "_i", precision = input_port.get_precision(), var_type = Signal.Local)
      io_map[input_tag] = input_signal
      if not input_tag in ["clk", "reset"]:
        input_signals[input_tag] = input_signal
    for output_port in self.implementation.get_output_port():
      output_tag = output_port.get_tag()
      output_signal = Signal(output_tag + "_o", precision = output_port.get_precision(), var_type = Signal.Local)
      io_map[output_tag] = output_signal
      output_signals[output_tag] = output_signal

    # building list of test cases
    tc_list = []

    self_component = self.implementation.get_component_object()
    self_instance = self_component(io_map = io_map, tag = "tested_entity")
    test_statement = Statement()

    # initializing random test case generator
    self.init_test_generator()

    # Appending standard test cases if required
    if self.auto_test_std:
      tc_list += self.standard_test_cases 

    for i in range(test_num):
      input_values = self.generate_test_case(input_signals, io_map, i, test_range)
      tc_list.append((input_values,None))

    for input_values, output_values in tc_list:
      input_msg = ""

      # Adding input setting
      for input_tag in input_values:
        input_signal = io_map[input_tag]
        # FIXME: correct value generation depending on signal precision
        input_value = input_values[input_tag]
        test_statement.add(ReferenceAssign(input_signal, Constant(input_value, precision = input_signal.get_precision())))
        value_msg = input_signal.get_precision().get_cst(input_value, language = VHDL_Code).replace('"',"'")
        value_msg += " / " + hex(input_signal.get_precision().get_base_format().get_integer_coding(input_value))
        input_msg += " {}={} ".format(input_tag, value_msg)
      test_statement.add(Wait(10))
      # Computing output values when necessary
      if output_values is None:
        output_values = self.numeric_emulate(input_values)
      # Adding output value comparison
      for output_tag in output_signals:
        output_signal = output_signals[output_tag]
        output_value  = Constant(output_values[output_tag], precision = output_signal.get_precision())
        value_msg = output_signal.get_precision().get_cst(output_values[output_tag], language = VHDL_Code).replace('"',"'")
        value_msg += " / " + hex(output_signal.get_precision().get_base_format().get_integer_coding(output_values[output_tag]))

        test_pass_cond = Comparison(
          output_signal,
          output_value,
          specifier = Comparison.Equal,
          precision = ML_Bool
        )

        test_statement.add(
            ConditionBlock(
                LogicalNot(
                    test_pass_cond,
                    precision = ML_Bool
                ),
                Report(
                    Concatenation(
                        " result for {}: ".format(output_tag),
                        Conversion(
                            TypeCast(
                                output_signal,
                                precision = ML_StdLogicVectorFormat(
                                    output_signal.get_precision().get_bit_size()
                                )
                             ),
                            precision = ML_String
                            ),
                        precision = ML_String
                    )
                )
            )
        )
        test_statement.add(
          Assert(
            test_pass_cond,
            "\"unexpected value for inputs {input_msg}, output {output_tag}, expecting {value_msg}, got: \"".format(input_msg = input_msg, output_tag = output_tag, value_msg = value_msg),
            severity = Assert.Failure
          )
        )


    testbench = CodeEntity("testbench") 
    test_process = Process(
      test_statement,
      # end of test
      Assert(
        Constant(0, precision = ML_Bool),
        " \"end of test, no error encountered \"",
        severity = Assert.Failure
      )
    )

    testbench_scheme = Statement(
      self_instance,
      test_process
    )

    testbench.add_process(testbench_scheme)

    return [testbench]

  @staticmethod
  def get_name():
    return ML_EntityBasis.function_name

  # list of input to be used for standard test validation
  standard_test_cases = []


def ML_Entity(name):
  new_class = type(name, (ML_EntityBasis,), {"entity_name": name})
  new_class.get_name = staticmethod(lambda: name) 
  return new_class

# end of Doxygen's ml_entity group
## @}

