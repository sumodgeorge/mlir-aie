
.PHONY: all clean

# TODO - Change this to env variable?
SYSROOT = /group/xrlabs/platforms/vck190-pynq-v2.7/sysroot

all: tutorial-8.exe

# Command line AIE kernel compile. See tutorial-2 for more info.
%.o: %.cc
	xchesscc -p me -P ${AIETOOLS_ROOT}/data/cervino/lib -c $<

# Command line mlir-aie compile script "aiecc.py"
# Sysroot and host target used to cross compile  host executable
# Local runtime_lib needed for testbench functions
tutorial-8.exe: aie.mlir test.cpp kernel1.o kernel2.o
	aiecc.py -j4 --sysroot=${SYSROOT} --host-target=aarch64-linux-gnu ./aie.mlir -I../../runtime_lib ../../runtime_lib/test_library.cpp ./test.cpp -o $@

clean:
	rm -rf acdc_project *elf *exe core* kernel*.o

#------------------------------------------------------------------------------
# Additional make targets for tutorial exercises
#------------------------------------------------------------------------------
tutorial-8_q3.exe: test.cpp ./answers/aie.mlir
	aiecc.py -j4 --sysroot=${SYSROOT} --host-target=aarch64-linux-gnu $(word 2,$^) -I../../runtime_lib ../../runtime_lib/test_library.cpp ./$< -o $@
