// RUN: aie-opt --aie-create-coremodule %s | FileCheck %s

// CHECK-LABEL: module @test_dma3 {
// CHECK:         %[[m33:.*]] = AIE.mem(3, 3) {
// CHECK:           %[[buf:.*]] = alloc() {id = 0 : i32} : memref<256xi32>
// CHECK:           %[[dmaSt:.*]] = AIE.dmaStart("S2MM0")
// CHECK:           ^[[dma0:.*]]:  // pred: ^bb0
// CHECK:             cond_br %[[dmaSt]], ^[[bd0:.*]], ^[[end:.*]]
// CHECK:           ^[[bd0]]:  // pred: ^[[dma0]]
// CHECK:             AIE.useToken @token0("Acquire", 3)
// CHECK:             AIE.dmaBd(<%[[buf]] : memref<256xi32>, 0, 256>, 0)
// CHECK:             AIE.useToken @token0("Release", 4)
// CHECK:             br ^[[end]]
// CHECK:           ^[[end]]:  // 3 preds: ^bb0, ^[[dma0]], ^[[bd0]]
// CHECK:             AIE.end
// CHECK:         }
// CHECK:         %[[m22:.*]] = AIE.mem(2, 2) {
// CHECK:           %[[buf:.*]] = alloc() {id = 0 : i32} : memref<256xi32>
// CHECK:           %[[dmaSt0:.*]] = AIE.dmaStart("S2MM0")
// CHECK:           %[[dmaSt1:.*]] = AIE.dmaStart("MM2S0")
// CHECK:           ^[[dma0:.*]]:  // pred: ^bb0
// CHECK:             cond_br %[[dmaSt0]], ^[[bd0:.*]], ^[[end:.*]]
// CHECK:           ^[[bd0]]:  // pred: ^[[dma0]]
// CHECK:             AIE.useToken @token0("Acquire", 1)
// CHECK:             AIE.dmaBd(<%[[buf]] : memref<256xi32>, 0, 256>, 0)
// CHECK:             AIE.useToken @token0("Release", 2)
// CHECK:             br ^[[end]]
// CHECK:           ^[[dma1:.*]]:  // pred: ^bb0
// CHECK:             cond_br %[[dmaSt1]], ^[[bd1:.*]], ^[[end]]
// CHECK:           ^[[bd1]]:  // pred: ^[[dma1]]
// CHECK:             AIE.useToken @token0("Acquire", 3)
// CHECK:             AIE.dmaBd(<%[[buf]] : memref<256xi32>, 0, 256>, 0)
// CHECK:             AIE.useToken @token0("Release", 4)
// CHECK:             br ^[[end]]
// CHECK:           ^[[end]]:  // 5 preds: ^bb0, ^[[dma0]], ^[[bd0]], ^[[dma1]], ^[[bd1]]
// CHECK:             AIE.end
// CHECK:         }
// CHECK:         %[[m11:.*]] = AIE.mem(1, 1) {
// CHECK:           %[[buf:.*]] = alloc() {id = 0 : i32} : memref<256xi32>
// CHECK:           %[[dmaS:.*]] = AIE.dmaStart("MM2S0")
// CHECK:           ^[[dma0:.*]]:  // pred: ^bb0
// CHECK:             cond_br %13, ^[[bd0:.*]], ^[[end:.*]]
// CHECK:           ^[[bd0]]:  // pred: ^[[dma0]]
// CHECK:             AIE.useToken @token0("Acquire", 1)
// CHECK:             AIE.dmaBd(<%[[buf]] : memref<256xi32>, 0, 256>, 0)
// CHECK:             AIE.useToken @token0("Release", 2)
// CHECK:             br ^[[end]]
// CHECK:           ^[[end]]:  // 3 preds: ^bb0, ^[[dma0]], ^[[bd0]]
// CHECK:             AIE.end
// CHECK:         }
// CHECK:         %[[c11:.*]] = AIE.core(1, 1)
// CHECK:         %[[c22:.*]] = AIE.core(2, 2)
// CHECK:         %[[c33:.*]] = AIE.core(3, 3)
// CHECK:         %[[buf0:.*]] = alloc() : memref<256xi32>
// CHECK:         %[[buf1:.*]] = alloc() : memref<256xi32>
// CHECK:         %[[buf2:.*]] = alloc() : memref<256xi32>
// CHECK:         AIE.token(0) {sym_name = "token0"}
// CHECK:         %[[cm11:.*]] = AIE.coreModule(%[[c11]], %[[m11]]) {
// CHECK:           %[[buf:.*]] = AIE.buffer(%[[m11]], 0) : memref<256xi32>
// CHECK:           AIE.useToken @token0("Acquire", 0)
// CHECK:           AIE.useToken @token0("Release", 1)
// CHECK:         }
// CHECK:         AIE.flow(%[[c11]], "DMA" : 0, %[[c22]], "DMA" : 0)
// CHECK:         %[[cm22:.*]] = AIE.coreModule(%[[c22]], %[[m22]]) {
// CHECK:           %[[buf:.*]] = AIE.buffer(%[[m22]], 0) : memref<256xi32>
// CHECK:           AIE.useToken @token0("Acquire", 2)
// CHECK:           AIE.useToken @token0("Release", 3)
// CHECK:         }
// CHECK:         AIE.flow(%[[c22]], "DMA" : 0, %[[c33]], "DMA" : 0)
// CHECK:         %[[cm33:.*]] = AIE.coreModule(%[[c33]], %[[m33]]) {
// CHECK:           %[[buf:.*]] = AIE.buffer(%[[m33]], 0) : memref<256xi32>
// CHECK:           AIE.useToken @token0("Acquire", 4)
// CHECK:           AIE.useToken @token0("Release", 5)
// CHECK:         }
// CHECK:       }

// Lowering Std::FuncOp and Std::CallOp with (aie.x, aie.y) attributes to AIE::CoreModuleOp
// Lowering AIE::memcpy to AIE::DMAStartOp and AIE::DMABDOp
// producer --> consumer/producer --> consumer
module @test_dma3 {
  %c11 = AIE.core(1, 1) // producer
  %c22 = AIE.core(2, 2) // consumer/producer
  %c33 = AIE.core(3, 3) // consumer

  %buf0 = alloc() : memref<256xi32>
  %buf1 = alloc() : memref<256xi32>
  %buf2 = alloc() : memref<256xi32>

  AIE.token(0) { sym_name="token0" }

  func @task0(%arg0: memref<256xi32>) -> () {
    AIE.useToken @token0("Acquire", 0)
    // code
    AIE.useToken @token0("Release", 1)
    return
  }

  func @task1(%arg0: memref<256xi32>) -> () {
    AIE.useToken @token0("Acquire", 2)
    // code
    AIE.useToken @token0("Release", 3)
    return
  }

  func @task2(%arg0: memref<256xi32>) -> () {
    AIE.useToken @token0("Acquire", 4)
    // code
    AIE.useToken @token0("Release", 5)
    return
  }

  call @task0(%buf0) { aie.x = 1, aie.y = 1 } : (memref<256xi32>) -> ()
  AIE.memcpy @token0(1, 2) (%c11 : <%buf0, 0, 256>, %c22 : <%buf1, 0, 256>) : (memref<256xi32>, memref<256xi32>)
  call @task1(%buf1) { aie.x = 2, aie.y = 2 } : (memref<256xi32>) -> ()
  AIE.memcpy @token0(3, 4) (%c22 : <%buf1, 0, 256>, %c33 : <%buf2, 0, 256>) : (memref<256xi32>, memref<256xi32>)
  call @task2(%buf2) { aie.x = 3, aie.y = 3 } : (memref<256xi32>) -> ()
}