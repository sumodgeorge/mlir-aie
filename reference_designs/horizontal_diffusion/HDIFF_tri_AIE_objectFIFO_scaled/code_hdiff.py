# (c) 2023 SAFARI Research Group at ETH Zurich, Gagandeep Singh, D-ITET

import sys
import re
import math
import random

noc_columns = [ 2, 3, 6, 7, 10, 11, 18, 19, 26, 27, 34, 35, 42, 43, 46, 47]


total_b_block=1 # only 1
b_block_depth=4 #set how many rows
input_rows=8 # data input per block row

hdiff_col=3 #columns
arraycols = 0# must be even until 32
broadcast_cores=0 # only 1-2
arrayrows = 0 # one for processing and one for shimDMA
startrow = 2
startcol = 0
bufsize = 256 # must fit in data memory
bufsize_flx1=512
bufsize_flx2=256
dram_bufsize_in=256*(input_rows)
dram_bufsize_out=256*2*b_block_depth

iter_i=0
iter_j=1
cur_noc_count=0
cur_noc_count_in=0
cur_noc_count_out=0
def main():
    global arrayrows
    global arraycols
    global bufsize

    print("Enabling %d block with depth %d" % (total_b_block,b_block_depth))

    rows = arrayrows  # row 0 is reserved
    cols = arraycols

    f = open("aie.mlir", "w+")
    # declare tile, column by row


    f.write("""//===- aie.mlir ------------------------------------------------*- MLIR -*-===//
// This file is licensed under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
// /*  (c) 2023 SAFARI Research Group at ETH Zurich, Gagandeep Singh, D-ITET             */
//
//===----------------------------------------------------------------------===//
//
// Note:
// RUN: aiecc.py --sysroot=%VITIS_SYSROOT% --host-target=aarch64-linux-gnu %s -I%aie_runtime_lib% %aie_runtime_lib%/test_library.cpp %S/test.cpp -o test.elf
// RUN: %run_on_board ./test.elf \n\n\n""")



    f.write("module @hdiff_bundle_%d {\n"%(total_b_block))
    def noc_div_two_channel(block):
        print(block)
        seg=2
        if block<seg:
           val= noc_columns[0]
        elif block>=seg and block<2*seg:
          val=  noc_columns[1]
        elif block>=2*seg and block<3*seg:
           val= noc_columns[2]
        elif block>=3*seg and block<4*seg:
           val= noc_columns[3]
        elif block>=4*seg and block<5*seg:
           val= noc_columns[4]
        elif block>=5*seg and block<6*seg:
           val= noc_columns[5]
        elif block>=6*seg and block<7*seg:
           val= noc_columns[6]   
        elif block>=7*seg and block<8*seg:
           val= noc_columns[7]   
        elif block>=8*seg and block<9*seg:
           val= noc_columns[8]   
        elif block>=9*seg and block<10*seg:
           val= noc_columns[9]   
        elif block>=10*seg and block<11*seg:
           val= noc_columns[10]   
        elif block>=11*seg and block<12*seg:
           val= noc_columns[11]   
        elif block>=12*seg and block<13*seg:
           val= noc_columns[12]   
        elif block>=13*seg and block<14*seg:
           val= noc_columns[13]   
        elif block>=14*seg and block<15*seg:
           val= noc_columns[14]   
        elif block>=15*seg:
           val= noc_columns[15]   
        return val
   
    
    # setting core tiles

    for b in range (0,total_b_block):
        f.write("//---Generating B-block %d---*-\n"%(b))
        for col in range (startcol, startcol + hdiff_col): # col 0 is reserved in aie
            f.write("//---col %d---*-\n"%(col+b*3))
            for row in range (startrow, startrow+b_block_depth): #
                f.write("  %%tile%d_%d = AIE.tile(%d, %d)\n" %(col+b*3, row, col+b*3, row))
        f.write("\n")
    f.write("\n")

    # setting NOC tiles 1 per two block
    noc_count=0
    for block in range (0, total_b_block): #
            if(block%2==0): 
                shim_place=noc_div_two_channel(block)
                f.write("//---NOC Tile %d---*-\n"%shim_place)
                f.write("  %%tile%d_%d = AIE.tile(%d, %d)\n" %(shim_place, 0, shim_place, 0))
            # noc_count=noc_count+1
    
    f.write("\n")
    
    
 
    

    # # def noc_place_min(cur, noc_i, noc_j):
    # #     global iter_i
    # #     global iter_j
    # #     # print("curre={}, noc_i{} noc_j{}".format(cur, noc_i, noc_j))
    # #     # print("iter_j{}".format(iter_j))
    # #     if cur>47:
    # #         return 47
    # #     if cur in [12,13,14]:
    # #         return 11
    # #     if cur in [20,21,22]:
    # #         return 19
    # #     elif cur>noc_i and iter_j<len(noc_columns)-1:
    # #         iter_i=iter_i+1;
    # #         iter_j=iter_j+1
    # #         return(noc_place_min(cur,noc_columns[iter_i],noc_columns[iter_j]))  
    # #     else:
    # #       return  noc_i

    
    # # for cur in range (0,50):
    # #     global iter_i
    # #     global iter_j
    # #     iter_i=0
    # #     iter_j=1
    # #     val=noc_place_min(cur,noc_columns[0],noc_columns[1])
    # #     # val=noc_place_cust(cur)
    # #     print("{}: NOC {}, Dist={}".format(cur, val,abs(val-cur)))
    # # row and column to generate for.  lastrow indicates that we shift one column to the right
    # # for the next core.
    
    def gagan_gen_buffer(block):
            f.write("//---Generating B%d buffers---*-\n"%block)
            # global cur_noc_count
            # if(cur_noc_count%2==0): 
            shim_place=noc_div_two_channel(block)
            # cur_noc_count=cur_noc_count+1
            broad_in=""
            symbol_in = ("block_%d_buf_in_shim_%d" % (block,shim_place))
            for row in range (startrow, startrow+b_block_depth): #
                for col in range (startcol, startcol + hdiff_col-1): # col 0 is reserved in aie
                    broad_in= broad_in+("%%tile%d_%d," % (col+block*3,row))
            bb_sym = broad_in[:-1]
            print(broad_in)
            f.write("  %%block_%d_buf_in_shim_%d = AIE.objectFifo.createObjectFifo(%%tile%d_0,{%s},%d) { sym_name = \"%s\" } : !AIE.objectFifo<memref<%dxi32>> //B block input\n" \
             %(block, shim_place,shim_place, bb_sym,input_rows+1,  symbol_in, bufsize))
            
            for row in range (startrow, startrow+b_block_depth): #
                    col=0+block*3
                    broad_in= broad_in+("%%tile%d_%d," % (col,row))
                    f.write("  %%block_%d_buf_row_%d_inter_lap= AIE.objectFifo.createObjectFifo(%%tile%d_%d,{%%tile%d_%d},5){ sym_name =\"block_%d_buf_row_%d_inter_lap\"} : !AIE.objectFifo<memref<%dxi32>>\n" \
                    %(block, row, col, row, col+1, row, block, row, bufsize))
                    
                    col=1+block*3
                    f.write("  %%block_%d_buf_row_%d_inter_flx1= AIE.objectFifo.createObjectFifo(%%tile%d_%d,{%%tile%d_%d},6) { sym_name =\"block_%d_buf_row_%d_inter_flx1\"} : !AIE.objectFifo<memref<%dxi32>>\n" \
                    %(block, row, col, row, col+1, row, block, row, bufsize_flx1))
                    col=2+block*3
                 
                    if(row==startrow+b_block_depth-3):
                        f.write("  %%block_%d_buf_out_shim_%d= AIE.objectFifo.createObjectFifo(%%tile%d_%d,{%%tile%d_%d},5){ sym_name =\"block_%d_buf_out_shim_%d\"} : !AIE.objectFifo<memref<%dxi32>> //B block output\n" \
                        %(block,  shim_place,col, row, shim_place, 0, block, shim_place, bufsize_flx2))
                        
                    else:
                        f.write("  %%block_%d_buf_row_%d_out_flx2= AIE.objectFifo.createObjectFifo(%%tile%d_%d,{%%tile%d_%d},2) { sym_name =\"block_%d_buf_row_%d_out_flx2\"} : !AIE.objectFifo<memref<%dxi32>>\n" \
                    %(block, row, col, row, col, b_block_depth+startrow-3, block, row, bufsize_flx2))
                        
                    f.write("\n")
            



            
    for b in range (0, total_b_block):
        
                gagan_gen_buffer(b)
            

    def gagan_gen_ddr(block):
            # print(bb)
            f.write("  %%ext_buffer_in_%d = AIE.external_buffer  {sym_name = \"ddr_buffer_in_%d\"}: memref<%d x i32>\n" %(block, block,   dram_bufsize_in))
            
            f.write("  %%ext_buffer_out_%d = AIE.external_buffer  {sym_name = \"ddr_buffer_out_%d\"}: memref<%d x i32>\n" %(block, block,  dram_bufsize_out))
            f.write("\n")

    for i in range (0, total_b_block): # col 0 is reserved in aie
            gagan_gen_ddr(i)
    

   
    
    def gagan_reg_buffer(block):
        global cur_noc_count
        if(block==0):
            print("making zero")
            cur_noc_count=0
        # if(cur_noc_count%2==0): 
        #     shim_place=noc_div_two_channel(cur_noc_count)
        # cur_noc_count=cur_noc_count+1
        shim_place=noc_div_two_channel(block)
        print(shim_place)
        f.write("  AIE.objectFifo.registerExternalBuffers(%%tile%d_0, %%block_%d_buf_in_shim_%d : !AIE.objectFifo<memref<%dxi32>>, {%%ext_buffer_in_%d}) : (memref<%dxi32>)\n"\
         %( shim_place,block, shim_place,bufsize,block,dram_bufsize_in))
    
        f.write("  AIE.objectFifo.registerExternalBuffers(%%tile%d_0, %%block_%d_buf_out_shim_%d : !AIE.objectFifo<memref<%dxi32>>, {%%ext_buffer_out_%d}) : (memref<%dxi32>)\n"\
         %( shim_place,block, shim_place,bufsize,block,dram_bufsize_out))
           
        f.write("\n")
        
       

    
    f.write("//Registering buffers\n")
   
    for i in range (0, total_b_block): # col 0 is reserved in aie
            gagan_reg_buffer(i)


    

    f.write("\n  func.func private @hdiff_lap(%AL: memref<256xi32>,%BL: memref<256xi32>, %CL:  memref<256xi32>, %DL: memref<256xi32>, %EL:  memref<256xi32>,  %OLL1: memref<256xi32>,  %OLL2: memref<256xi32>,  %OLL3: memref<256xi32>,  %OLL4: memref<256xi32>) -> ()\n")
    f.write("  func.func private @hdiff_flux1(%AF: memref<256xi32>,%BF: memref<256xi32>, %CF:  memref<256xi32>,   %OLF1: memref<256xi32>,  %OLF2: memref<256xi32>,  %OLF3: memref<256xi32>,  %OLF4: memref<256xi32>,  %OFI1: memref<512xi32>,  %OFI2: memref<512xi32>,  %OFI3: memref<512xi32>,  %OFI4: memref<512xi32>,  %OFI5: memref<512xi32>) -> ()\n")
    f.write("  func.func private @hdiff_flux2( %Inter1: memref<512xi32>,%Inter2: memref<512xi32>, %Inter3: memref<512xi32>,%Inter4: memref<512xi32>,%Inter5: memref<512xi32>,  %Out: memref<256xi32>) -> ()\n")


    f.write("\n")
    def gagan_gen_lap_core(block, col, row,shim_place):
       
            f.write("  %%block_%d_core%d_%d = AIE.core(%%tile%d_%d) {\n" %(block,col, row, col, row))
            f.write("    %lb = arith.constant 0 : index\n")
            f.write("    %ub = arith.constant 2 : index\n")
            f.write("    %step = arith.constant 1 : index\n")
            f.write("    scf.for %iv = %lb to %ub step %step {  \n")
            f.write("      %%obj_in_subview = AIE.objectFifo.acquire<Consume>(%%block_%d_buf_in_shim_%d: !AIE.objectFifo<memref<%dxi32>>, %d) : !AIE.objectFifoSubview<memref<%dxi32>>\n" %(block,shim_place, bufsize,input_rows,bufsize))
            f.write("      %%row0 = AIE.objectFifo.subview.access %%obj_in_subview[%d] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n" %(row-startrow,bufsize,bufsize))
            f.write("      %%row1 = AIE.objectFifo.subview.access %%obj_in_subview[%d] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n" %(row-startrow+1,bufsize,bufsize))
            f.write("      %%row2 = AIE.objectFifo.subview.access %%obj_in_subview[%d] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n" %(row-startrow+2,bufsize,bufsize))
            f.write("      %%row3 = AIE.objectFifo.subview.access %%obj_in_subview[%d] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n" %(row-startrow+3,bufsize,bufsize))
            f.write("      %%row4 = AIE.objectFifo.subview.access %%obj_in_subview[%d] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n\n" %(row-startrow+4,bufsize,bufsize))
   
            f.write("      %%obj_out_subview_lap = AIE.objectFifo.acquire<Produce>(%%block_%d_buf_row_%d_inter_lap: !AIE.objectFifo<memref<%dxi32>>, 4): !AIE.objectFifoSubview<memref<%dxi32>>\n" %(block, row,bufsize,bufsize))
            f.write("      %obj_out_lap1 = AIE.objectFifo.subview.access %obj_out_subview_lap[0] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
            f.write("      %obj_out_lap2 = AIE.objectFifo.subview.access %obj_out_subview_lap[1] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
            f.write("      %obj_out_lap3 = AIE.objectFifo.subview.access %obj_out_subview_lap[2] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
            f.write("      %obj_out_lap4 = AIE.objectFifo.subview.access %obj_out_subview_lap[3] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n\n")
            
            f.write("      func.call @hdiff_lap(%row0,%row1,%row2,%row3,%row4,%obj_out_lap1,%obj_out_lap2,%obj_out_lap3,%obj_out_lap4) : (memref<256xi32>,memref<256xi32>, memref<256xi32>, memref<256xi32>, memref<256xi32>,  memref<256xi32>,  memref<256xi32>,  memref<256xi32>,  memref<256xi32>) -> ()\n\n")
            f.write("      AIE.objectFifo.release<Consume>(%%block_%d_buf_in_shim_%d: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, shim_place,bufsize))
            f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_inter_lap: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,bufsize))
            f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_inter_lap: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,bufsize))
            f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_inter_lap: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,bufsize))
            f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_inter_lap: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,bufsize))
            f.write("    }\n")
            f.write("    AIE.objectFifo.release<Consume>(%%block_%d_buf_in_shim_%d: !AIE.objectFifo<memref<%dxi32>>, 4)\n" %(block, shim_place,bufsize))
            f.write("    AIE.end\n")
            f.write("  } { link_with=\"hdiff_lap.o\" }\n\n")

    def gagan_gen_flx1_core(block, col, row,shim_place):
       
            f.write("  %%block_%d_core%d_%d = AIE.core(%%tile%d_%d) {\n" %(block,col, row, col, row))
            f.write("    %lb = arith.constant 0 : index\n")
            f.write("    %ub = arith.constant 2 : index\n")
            f.write("    %step = arith.constant 1 : index\n")
            f.write("    scf.for %iv = %lb to %ub step %step {  \n")
            f.write("      %%obj_in_subview = AIE.objectFifo.acquire<Consume>(%%block_%d_buf_in_shim_%d: !AIE.objectFifo<memref<%dxi32>>, %d) : !AIE.objectFifoSubview<memref<%dxi32>>\n" %(block,shim_place, bufsize,input_rows,bufsize))
            # f.write("      %%row0 = AIE.objectFifo.subview.access %%obj_in_subview[0] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n" %(bufsize,bufsize))
            f.write("      %%row1 = AIE.objectFifo.subview.access %%obj_in_subview[%d] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n" %(row-startrow+1,bufsize,bufsize))
            f.write("      %%row2 = AIE.objectFifo.subview.access %%obj_in_subview[%d] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n" %(row-startrow+2,bufsize,bufsize))
            f.write("      %%row3 = AIE.objectFifo.subview.access %%obj_in_subview[%d] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n\n" %(row-startrow+3,bufsize,bufsize))
            # f.write("      %%row4 = AIE.objectFifo.subview.access %%obj_in_subview[4] : !AIE.objectFifoSubview<memref<%dxi32>> -> memref<%dxi32>\n" %(bufsize,bufsize))
   
            f.write("      %%obj_out_subview_lap = AIE.objectFifo.acquire<Consume>(%%block_%d_buf_row_%d_inter_lap: !AIE.objectFifo<memref<%dxi32>>, 4): !AIE.objectFifoSubview<memref<%dxi32>>\n" %(block, row,bufsize,bufsize))
            f.write("      %obj_out_lap1 = AIE.objectFifo.subview.access %obj_out_subview_lap[0] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
            f.write("      %obj_out_lap2 = AIE.objectFifo.subview.access %obj_out_subview_lap[1] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
            f.write("      %obj_out_lap3 = AIE.objectFifo.subview.access %obj_out_subview_lap[2] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
            f.write("      %obj_out_lap4 = AIE.objectFifo.subview.access %obj_out_subview_lap[3] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n\n")

            f.write("      %%obj_out_subview_flux1 = AIE.objectFifo.acquire<Produce>(%%block_%d_buf_row_%d_inter_flx1: !AIE.objectFifo<memref<%dxi32>>, 5): !AIE.objectFifoSubview<memref<%dxi32>>\n" %(block, row,bufsize_flx1,bufsize_flx1))
            f.write("      %obj_out_flux_inter1 = AIE.objectFifo.subview.access %obj_out_subview_flux1[0] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n")
            f.write("      %obj_out_flux_inter2 = AIE.objectFifo.subview.access %obj_out_subview_flux1[1] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n")
            f.write("      %obj_out_flux_inter3 = AIE.objectFifo.subview.access %obj_out_subview_flux1[2] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n")
            f.write("      %obj_out_flux_inter4 = AIE.objectFifo.subview.access %obj_out_subview_flux1[3] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n")
            f.write("      %obj_out_flux_inter5 = AIE.objectFifo.subview.access %obj_out_subview_flux1[4] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n\n")

            f.write("      func.call @hdiff_flux1(%row1,%row2,%row3,%obj_out_lap1,%obj_out_lap2,%obj_out_lap3,%obj_out_lap4, %obj_out_flux_inter1 , %obj_out_flux_inter2, %obj_out_flux_inter3, %obj_out_flux_inter4, %obj_out_flux_inter5) : (memref<256xi32>,memref<256xi32>, memref<256xi32>, memref<256xi32>, memref<256xi32>, memref<256xi32>,  memref<256xi32>,  memref<512xi32>,  memref<512xi32>,  memref<512xi32>,  memref<512xi32>,  memref<512xi32>) -> ()\n\n")
            # f.write("      AIE.objectFifo.release<Consume>(%%block_%d_buf_in_shim_%d: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, shim_place,bufsize))
            
            f.write("      AIE.objectFifo.release<Consume>(%%block_%d_buf_row_%d_inter_lap: !AIE.objectFifo<memref<%dxi32>>, 4)\n" %(block, row,bufsize))

            f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_inter_flx1: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,bufsize_flx1))
            f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_inter_flx1: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,bufsize_flx1))
            f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_inter_flx1: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,bufsize_flx1))
            f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_inter_flx1: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,bufsize_flx1))
            f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_inter_flx1: !AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,bufsize_flx1))
            f.write("    }\n")
            f.write("    AIE.objectFifo.release<Consume>(%%block_%d_buf_in_shim_%d: !AIE.objectFifo<memref<%dxi32>>, 4)\n" %(block, shim_place,bufsize))
            f.write("    AIE.end\n")
            f.write("  } { link_with=\"hdiff_flux1.o\" }\n\n")

    def gagan_gen_flx2_core(block, col, row,shim_place):
            if(row==startrow+b_block_depth-3):
                f.write("  // Gathering Tile\n")
            f.write("  %%block_%d_core%d_%d = AIE.core(%%tile%d_%d) {\n" %(block,col, row, col, row))
            f.write("    %lb = arith.constant 0 : index\n")
            f.write("    %ub = arith.constant 2 : index\n")
            f.write("    %step = arith.constant 1 : index\n")
            f.write("    scf.for %iv = %lb to %ub step %step {  \n")

            f.write("      %%obj_out_subview_flux_inter1 = AIE.objectFifo.acquire<Consume>(%%block_%d_buf_row_%d_inter_flx1: !AIE.objectFifo<memref<%dxi32>>, 5): !AIE.objectFifoSubview<memref<%dxi32>>\n" %(block, row,bufsize_flx1,bufsize_flx1))
            f.write("      %obj_flux_inter_element1 = AIE.objectFifo.subview.access %obj_out_subview_flux_inter1[0] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n")
            f.write("      %obj_flux_inter_element2 = AIE.objectFifo.subview.access %obj_out_subview_flux_inter1[1] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n")
            f.write("      %obj_flux_inter_element3 = AIE.objectFifo.subview.access %obj_out_subview_flux_inter1[2] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n")
            f.write("      %obj_flux_inter_element4 = AIE.objectFifo.subview.access %obj_out_subview_flux_inter1[3] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n")
            f.write("      %obj_flux_inter_element5 = AIE.objectFifo.subview.access %obj_out_subview_flux_inter1[4] : !AIE.objectFifoSubview<memref<512xi32>> -> memref<512xi32>\n\n")
            if(row==startrow+b_block_depth-3):
                f.write("      %%obj_out_subview_flux = AIE.objectFifo.acquire<Produce>(%%block_%d_buf_out_shim_%d: !AIE.objectFifo<memref<%dxi32>>, 5): !AIE.objectFifoSubview<memref<%dxi32>>\n" %(block, shim_place,256,256))
                
                
                f.write("  // Acquire all elements and add in order\n")
                f.write("      %obj_out_flux_element0 = AIE.objectFifo.subview.access %obj_out_subview_flux[0] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
                f.write("      %obj_out_flux_element1 = AIE.objectFifo.subview.access %obj_out_subview_flux[1] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
                f.write("      %obj_out_flux_element2 = AIE.objectFifo.subview.access %obj_out_subview_flux[2] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
                f.write("      %obj_out_flux_element3 = AIE.objectFifo.subview.access %obj_out_subview_flux[3] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n")
                
                f.write("  // Acquiring outputs from other flux\n")
                for order in range (startrow,startrow+broadcast_cores+b_block_depth):  
                    if(order!=startrow+b_block_depth-3):
                        f.write("      %%obj_out_subview_flux%d = AIE.objectFifo.acquire<Consume>(%%block_%d_buf_row_%d_out_flx2: !AIE.objectFifo<memref<%dxi32>>, 1): !AIE.objectFifoSubview<memref<%dxi32>>\n" %(order,block, order,256,256))
                        f.write("      %%final_out_from%d = AIE.objectFifo.subview.access %%obj_out_subview_flux%d[0] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n\n"%(order,order))
                
                f.write("  // Ordering and copying data to gather tile (src-->dst)\n")
                f.write("      memref.copy %final_out_from2 , %obj_out_flux_element0 : memref<256xi32> to memref<256xi32>\n")
                f.write("      memref.copy %final_out_from4 , %obj_out_flux_element2 : memref<256xi32> to memref<256xi32>\n")
                f.write("      memref.copy %final_out_from5 , %obj_out_flux_element3 : memref<256xi32> to memref<256xi32>\n")
                ###############
            else:
                f.write("      %%obj_out_subview_flux = AIE.objectFifo.acquire<Produce>(%%block_%d_buf_row_%d_out_flx2: !AIE.objectFifo<memref<%dxi32>>, 1): !AIE.objectFifoSubview<memref<%dxi32>>\n" %(block, row,256,256))
                f.write("      %obj_out_flux_element1 = AIE.objectFifo.subview.access %obj_out_subview_flux[0] : !AIE.objectFifoSubview<memref<256xi32>> -> memref<256xi32>\n\n")

            f.write("      func.call @hdiff_flux2(%obj_flux_inter_element1, %obj_flux_inter_element2,%obj_flux_inter_element3, %obj_flux_inter_element4, %obj_flux_inter_element5,  %obj_out_flux_element1 ) : ( memref<512xi32>,  memref<512xi32>, memref<512xi32>, memref<512xi32>, memref<512xi32>, memref<256xi32>) -> ()\n\n")
       
            f.write("      AIE.objectFifo.release<Consume>(%%block_%d_buf_row_%d_inter_flx1 :!AIE.objectFifo<memref<%dxi32>>, 4)\n" %(block, row,bufsize_flx1))
            
            if(row==startrow+b_block_depth-3):
                # addded for output ordering
                 ###############
                f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_out_shim_%d :!AIE.objectFifo<memref<%dxi32>>, 4)\n" %(block, shim_place,256))
            else:
                f.write("      AIE.objectFifo.release<Produce>(%%block_%d_buf_row_%d_out_flx2 :!AIE.objectFifo<memref<%dxi32>>, 1)\n" %(block, row,256))
          
            f.write("    }\n")

            f.write("    AIE.end\n")
            f.write("  } { link_with=\"hdiff_flux2.o\" }\n\n")

    for b in range (0, total_b_block): # col 0 is reserved in aie
        # for c in range (startcol, startcol + arraycols+hdiff_col): # col 0 is reserved in aie
            for r in range (startrow,startrow+broadcast_cores+b_block_depth):
                shim_place=noc_div_two_channel(b)
                gagan_gen_lap_core(b,0+b*3,r,shim_place)
                gagan_gen_flx1_core(b,1+b*3,r,shim_place)
                gagan_gen_flx2_core(b,2+b*3,r,shim_place)
               

    # # for i in range (0, 64): # col 0 is reserved in aie
    # #     f.write("mlir_aie_sync_mem_dev(_xaie, %d);\n "%(i) )

    # # for i in range (0, 32): # col 0 is reserved in aie
    # #     f.write("mlir_aie_external_set_addr_ddr_buffer_in_%d((u64)ddr_ptr_in_%d); \n "%(i,i) )
    
    # # for i in range (0, 32): # col 0 is reserved in aie
    # #     f.write("mlir_aie_external_set_addr_ddr_buffer_out_%d_2((u64)ddr_ptr_out_%d_2); \n "%(i,i) )
    

    # # for i in range (32,64): # col 0 is reserved in aie
    # #     f.write("mlir_aie_sync_mem_cpu(_xaie, %d); //// only used in libaiev2 //sync up with output\n "%(i) )
    
    f.write("}\n")


if __name__ == "__main__":
    main()