#!/usr/bin/env python3
"""
Unit tests for realtime.py utility functions
"""

import pytest
import numpy as np
import base64
from realtime import (
    float_to_16bit_pcm,
    base64_to_array_buffer,
    array_buffer_to_base64,
    merge_int16_arrays
)


class TestFloat16BitPCM:
    """Test float_to_16bit_pcm conversion"""
    
    def test_basic_conversion(self):
        """Test basic float32 to int16 conversion"""
        float_array = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        result = float_to_16bit_pcm(float_array)
        
        assert result.dtype == np.int16
        assert len(result) == len(float_array)
        assert result[0] == 0
        assert result[3] == 32767  # 1.0 * 32767
        assert result[4] == -32767  # -1.0 * 32767
    
    def test_clipping(self):
        """Test that values outside [-1, 1] are clipped"""
        float_array = np.array([2.0, -2.0, 1.5, -1.5], dtype=np.float32)
        result = float_to_16bit_pcm(float_array)
        
        # All values should be clipped to [-32767, 32767]
        assert result[0] == 32767  # 2.0 clipped to 1.0
        assert result[1] == -32767  # -2.0 clipped to -1.0
        assert result[2] == 32767  # 1.5 clipped to 1.0
        assert result[3] == -32767  # -1.5 clipped to -1.0
    
    def test_empty_array(self):
        """Test conversion of empty array"""
        float_array = np.array([], dtype=np.float32)
        result = float_to_16bit_pcm(float_array)
        
        assert result.dtype == np.int16
        assert len(result) == 0


class TestBase64ArrayConversion:
    """Test base64 and array buffer conversion functions"""
    
    def test_base64_to_array_buffer(self):
        """Test converting base64 string to numpy array"""
        # Create a base64 encoded string
        test_data = b"Hello, World!"
        base64_string = base64.b64encode(test_data).decode('utf-8')
        
        result = base64_to_array_buffer(base64_string)
        
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.uint8
        assert result.tobytes() == test_data
    
    def test_array_buffer_to_base64_float32(self):
        """Test converting float32 array to base64"""
        float_array = np.array([0.0, 0.5, -0.5, 1.0], dtype=np.float32)
        result = array_buffer_to_base64(float_array)
        
        assert isinstance(result, str)
        # Decode and verify it's valid base64
        decoded = base64.b64decode(result)
        assert len(decoded) > 0
    
    def test_array_buffer_to_base64_int16(self):
        """Test converting int16 array to base64"""
        int_array = np.array([0, 100, -100, 32767], dtype=np.int16)
        result = array_buffer_to_base64(int_array)
        
        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        assert len(decoded) == int_array.nbytes
    
    def test_array_buffer_to_base64_uint8(self):
        """Test converting uint8 array to base64"""
        uint_array = np.array([0, 127, 255], dtype=np.uint8)
        result = array_buffer_to_base64(uint_array)
        
        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        assert decoded == uint_array.tobytes()
    
    def test_round_trip_conversion(self):
        """Test converting array to base64 and back"""
        original_data = np.array([1, 2, 3, 4, 5], dtype=np.uint8)
        
        # Convert to base64
        base64_string = array_buffer_to_base64(original_data)
        
        # Convert back to array
        result = base64_to_array_buffer(base64_string)
        
        np.testing.assert_array_equal(result, original_data)


class TestMergeInt16Arrays:
    """Test merge_int16_arrays function"""
    
    def test_basic_merge(self):
        """Test basic merging of two int16 arrays"""
        left = np.array([1, 2, 3], dtype=np.int16)
        right = np.array([4, 5, 6], dtype=np.int16)
        
        result = merge_int16_arrays(left, right)
        
        expected = np.array([1, 2, 3, 4, 5, 6], dtype=np.int16)
        np.testing.assert_array_equal(result, expected)
    
    def test_merge_empty_arrays(self):
        """Test merging with empty arrays"""
        left = np.array([1, 2, 3], dtype=np.int16)
        right = np.array([], dtype=np.int16)
        
        result = merge_int16_arrays(left, right)
        np.testing.assert_array_equal(result, left)
        
        left_empty = np.array([], dtype=np.int16)
        right_full = np.array([4, 5, 6], dtype=np.int16)
        
        result2 = merge_int16_arrays(left_empty, right_full)
        np.testing.assert_array_equal(result2, right_full)
    
    def test_merge_invalid_dtype(self):
        """Test that merging non-int16 arrays raises error"""
        left = np.array([1, 2, 3], dtype=np.int32)
        right = np.array([4, 5, 6], dtype=np.int16)
        
        with pytest.raises(ValueError):
            merge_int16_arrays(left, right)
    
    def test_merge_non_array(self):
        """Test that merging non-arrays raises error"""
        left = [1, 2, 3]
        right = np.array([4, 5, 6], dtype=np.int16)
        
        with pytest.raises(ValueError):
            merge_int16_arrays(left, right)
