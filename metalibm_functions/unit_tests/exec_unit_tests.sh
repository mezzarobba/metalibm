python $ML_SRC_DIR/metalibm_functions/unit_tests/fixed_point.py --target fixed_point &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/function_emulate.py --target mpfr_backend &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/function_formats.py --target mpfr_backend &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/gappa_code.py &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/loop_operation.py &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/opencl_code.py &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/payne_hanek.py --precision binary64 &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/pointer_manipulation.py &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/static_vectorization.py --target vector &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/vector_code.py --target vector &&\
python $ML_SRC_DIR/metalibm_functions/unit_tests/call_externalization.py
