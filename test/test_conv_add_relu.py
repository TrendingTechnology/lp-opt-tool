import unittest
import tensorflow as tf
import numpy as np
import copy
from tensorflow.python.framework import graph_util
from ilit.adaptor.tf_utils.quantize_graph.quantize_graph_common import QuantizeGraphHelper
from ilit.adaptor.tf_utils.quantize_graph.quantize_graph_for_intel_cpu import QuantizeGraphForIntel

class TestConvAddRelu(unittest.TestCase):
    def test_conv_add_relu(self):
        tf.compat.v1.disable_eager_execution()
        x = tf.compat.v1.placeholder(tf.float32, [1, 224, 224, 3], name="input")
        conv_weights = tf.compat.v1.get_variable("weight", [3, 3, 3, 32],
                                                initializer=tf.compat.v1.random_normal_initializer())
        conv_bias = tf.compat.v1.get_variable("bias", [32],
                                            initializer=tf.compat.v1.random_normal_initializer())
        conv1 = tf.nn.conv2d(x, conv_weights, strides=[1, 1, 1, 1], padding="SAME")
        conv_bias=tf.math.add(conv1, conv_bias)
        relu=tf.nn.relu(conv_bias)
        with tf.compat.v1.Session() as sess:
            sess.run(tf.compat.v1.global_variables_initializer())
            output_graph_def = graph_util.convert_variables_to_constants(
                sess=sess,
                input_graph_def=sess.graph_def,
                output_node_names=[relu.name.split(':')[0]])
            output_graph_def = QuantizeGraphHelper.remove_training_nodes(
                output_graph_def, protected_nodes=[relu.name.split(':')[0]])
            graph_def = copy.deepcopy(output_graph_def)
            inputs = ['input']
            outputs = [relu.name.split(':')[0]]
            op_wise_config = {
                "Conv2D": (False, 'minmax', False),
            }
            graph_def=output_graph_def
            fold_graph_def = QuantizeGraphForIntel(output_graph_def,outputs,
                                                    op_wise_config,
                                                    'cpu').do_transform()
            found_QuantizedConv2DWithBiasAndRelu = False
            for i in fold_graph_def.node:
                if i.op == 'QuantizedConv2DWithBiasAndRelu':
                    found_QuantizedConv2DWithBiasAndRelu = True
                    break
            self.assertEqual(found_QuantizedConv2DWithBiasAndRelu, True)
 
if __name__ == "__main__":
    unittest.main()
