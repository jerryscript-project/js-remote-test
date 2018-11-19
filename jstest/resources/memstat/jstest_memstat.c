/* Copyright 2018-present Samsung Electronics Co., Ltd. and other contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
 * Memory statistic for system allocator.
 *
 * When allocating a chunk of memory, the real size (required memory with padding) is
 * located in a descriptor (mm_freenode_s) before the allocated memory area:
 *
 *    struct mm_freenode_s
 *    {
 *        mmsize_t size;        // Size of the chunk
 *        mmsize_t preceding;   // Size of the preceding chunk
 *        ...
 *    };
 *
 * +---------------+--------------------------------------+
 * | mm_freenode_s |        allocated memory chunk        |
 * +---------------+--------------------------------------+
 *                 ^
 *                 pointer to the data
 *
 * Note: on NuttX and TizenRT, the `size` variable contains the size of the
 * mm_freenode_s as well, but that is not calculated into the statistic.
 */
#if defined(JSTEST_MEMSTAT_ENABLED)
#include <stdio.h>
#include <stdlib.h>

#if defined(__NUTTX__)
#include <nuttx/mm/mm.h>
#elif defined(__TIZENRT__)
#include <tinyara/mm/mm.h>
#else
#error "The current target is not supported to track the memory consumption."
#endif

static size_t allocated_bytes = 0;
static size_t peak_allocated_bytes = 0;


static size_t read_memsize(char* ptr) {
  struct mm_freenode_s* node;

  if (ptr == NULL) {
    return 0;
  }

  node = (struct mm_freenode_s*)(ptr - SIZEOF_MM_ALLOCNODE);
  // Note: the allocnode descriptor size is not calculated
  // into the allocated memory.
  return node->size - SIZEOF_MM_ALLOCNODE;
}


static void mem_stat_alloc(void* ptr)
{
  allocated_bytes += read_memsize(ptr);

  if (allocated_bytes > peak_allocated_bytes) {
    peak_allocated_bytes = allocated_bytes;
  }
}


static void mem_stat_free(void* ptr)
{
  allocated_bytes -= read_memsize(ptr);
}


void* jstest_malloc(size_t size) {
  void* mem = malloc(size);

  mem_stat_alloc(mem);

  return mem;
}


void* jstest_calloc(size_t n, size_t elem_size) {
  void* mem = calloc(n, elem_size);

  mem_stat_alloc(mem);

  return mem;
}


void* jstest_realloc(void* oldmem, size_t size) {
  mem_stat_free(oldmem);

  void* newmem = realloc(oldmem, size);

  mem_stat_alloc(newmem);

  return newmem;
}


void jstest_free(void *mem) {
  mem_stat_free(mem);

  free(mem);
}


void print_mem_stat() {
  printf("Heap stats:\n");
  printf("  Malloc peak allocated: %u bytes\n", peak_allocated_bytes);
}


// Define custom allocator functions for mbedtls of TizenRT.
void *(*mbedtls_calloc)(size_t n, size_t size) = jstest_calloc;
void (*mbedtls_free)(void *ptr) = jstest_free;

#endif /* JSTEST_MEMSTAT_ENABLED */
