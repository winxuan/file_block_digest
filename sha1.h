/*
 * MIT License
 *
 * Copyright (c) 2022 WeCom-Open
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
#pragma once

#include <stdint.h>  // 替换<sys/types.h>，确保uint32_t定义

namespace file_block_digest {
typedef struct {
  union {
    uint32_t h0;  // 替换u_int32_t为uint32_t
    uint32_t state[5];
  };
  uint32_t count[2];
  unsigned char buffer[64];
} SHA_CTX;

void SHA1_Init(SHA_CTX* context);
void SHA1_Update(SHA_CTX* context, const unsigned char* data, uint32_t len);
void SHA1_Final(unsigned char digest[20], SHA_CTX* context);

}  // namespace file_block_digest