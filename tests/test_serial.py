# -------------------------------------------------------------------
# Copyright 2021 Virtex authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.
# -------------------------------------------------------------------

import time

import orjson
import numpy as np
import pandas as pd

from virtex.serial import *
from virtex.serial.pandas import encode_pandas, decode_pandas
from virtex.serial.numpy import encode_numpy, decode_numpy


def test_numpy():
    x = np.random.random((1000, 1000))
    xb = encode_numpy(x)
    xd = decode_numpy(xb)
    assert isinstance(xb, str)
    assert np.all(x == xd)


def test_pandas():
    x = pd.DataFrame(data=[[0.1, 3, 'a'],
                           [7.2, 10, 'b']],
                     columns=['x1', 'x2', 'y'])
    xb = encode_pandas(x)
    xd = decode_pandas(xb)
    assert xd.equals(x)


def test_PIL(test_image_PIL):
    img_enc = encode_pil(test_image_PIL)
    img_dec = decode_pil(img_enc)
    im1 = np.asarray(test_image_PIL)
    im2 = np.asarray(img_dec)
    assert np.array_equal(im1, im2), \
        print(np.sum(im1 - im2, keepdims=False))


def test_PIL_from_bytes(test_image_bytes, test_image_PIL):
    img_enc = encode_bytes(test_image_bytes)
    img_dec = decode_pil_from_bytes(img_enc)
    im1 = np.asarray(test_image_PIL)
    im2 = np.asarray(img_dec)
    assert np.array_equal(im1, im2), \
        print(np.sum(im1 - im2, keepdims=False))


def test_check_numpy_serialization_speed():

    """
    orjson has built-in numpy serialization. It is faster than
    the base64<-pickle<-python-object scheme for encoding, but
    slower for decoding of larger numerical arrays; since we
    are primarily interested in decoding speed in Virtex, with
    the assumption being that heavy lifting for most virtex
    use cases will be decoding numerical input data on the
    server, virtex opts to use the base64 encoding of the
    pickled object. This test is a check to ensure that we
    become aware of any future changes made to these libraries
    that impact performance.
    """

    data = [np.random.random((1, 3, 32, 32)) for _ in range(25)]

    t0 = time.time()
    enc_orjson = orjson.dumps(data, option=orjson.OPT_SERIALIZE_NUMPY)
    t1 = time.time()
    t_orjson = t1 - t0

    t0 = time.time()
    enc_pickle = encode_numpy(data)
    t1 = time.time()
    t_pickle = t1 - t0

    assert (t_pickle / t_orjson) < 2.25

    t0 = time.time()
    orjson.loads(enc_orjson)
    t1 = time.time()
    t_orjson = t1 - t0

    t0 = time.time()
    decode_numpy(enc_pickle)
    t1 = time.time()
    t_pickle = t1 - t0

    assert (t_pickle / t_orjson) < 0.55
