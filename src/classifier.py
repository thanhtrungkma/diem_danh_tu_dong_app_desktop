"""An example of how to use your own dataset to train a classifier that recognizes people.
"""
# MIT License
# 
# Copyright (c) 2016 David Sandberg
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import timedelta

import tensorflow as tf
import numpy as np
import argparse
import facenet
import os
import sys
import math
import pickle
from sklearn.svm import SVC
from timeit import default_timer as timer
from .facenet import *
from src.align_dataset_mtcnn import *

def trainClassifier(data_dir,
                    model,
                    classifier_filename,
                    use_split_dataset=None,
                    batch_size=1000,
                    image_size=160,
                    seed=666,
                    min_nrof_images_per_class=20,
                    nrof_train_images_per_class=10):
    with tf.Graph().as_default():

        with tf.compat.v1.Session() as sess:

            np.random.seed(seed=seed)

            if use_split_dataset:
                dataset_tmp = get_dataset(data_dir)
                train_set, test_set = split_dataset(dataset_tmp, min_nrof_images_per_class, nrof_train_images_per_class)
                dataset = train_set
            else:
                dataset = get_dataset(data_dir)

            # Check that there are at least one training image per class
            for cls in dataset:
                assert (len(cls.image_paths) > 0, 'There must be at least one image for each class in the dataset')

            paths, labels = get_image_paths_and_labels(dataset)

            print('Number of classes: %d' % len(dataset))
            print('Number of images: %d' % len(paths))

            # Load the model
            print('Loading feature extraction model')
            load_model(model)

            # Get input and output tensors
            images_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.compat.v1.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name("phase_train:0")
            embedding_size = embeddings.get_shape()[1]

            # Run forward pass to calculate embeddings
            print('Calculating features for images')
            nrof_images = len(paths)
            nrof_batches_per_epoch = int(math.ceil(1.0 * nrof_images / batch_size))
            emb_array = np.zeros((nrof_images, embedding_size))
            for i in range(nrof_batches_per_epoch):
                start_index = i * batch_size
                end_index = min((i + 1) * batch_size, nrof_images)
                paths_batch = paths[start_index:end_index]
                images = load_data(paths_batch, False, False, image_size)
                feed_dict = {images_placeholder: images, phase_train_placeholder: False}
                emb_array[start_index:end_index, :] = sess.run(embeddings, feed_dict=feed_dict)

            classifier_filename_exp = os.path.expanduser(classifier_filename)

            print('Training classifier')
            model = SVC(kernel='linear', probability=True)
            model.fit(emb_array, labels)

            # Create a list of class names
            class_names = [cls.name.replace('_', ' ') for cls in dataset]

            # Saving classifier model
            with open(classifier_filename_exp, 'wb') as outfile:
                pickle.dump((model, class_names), outfile)
            print('Saved classifier model to file "%s"' % classifier_filename_exp)


def split_dataset(dataset, min_nrof_images_per_class, nrof_train_images_per_class):
    train_set = []
    test_set = []
    for cls in dataset:
        paths = cls.image_paths
        # Remove classes with less than min_nrof_images_per_class
        if len(paths) >= min_nrof_images_per_class:
            np.random.shuffle(paths)
            train_set.append(ImageClass(cls.name, paths[:nrof_train_images_per_class]))
            test_set.append(ImageClass(cls.name, paths[nrof_train_images_per_class:]))
    return train_set, test_set


# def parse_arguments(argv):
#     parser = argparse.ArgumentParser()  
#
#     parser.add_argument('mode', type=str, choices=['TRAIN', 'CLASSIFY'],
#         help='Indicates if a new classifier should be trained or a classification ' +
#         'model should be used for classification', default='CLASSIFY')
#     parser.add_argument('data_dir', type=str,
#         help='Path to the data directory containing aligned LFW face patches.')
#     parser.add_argument('model', type=str,
#         help='Could be either a directory containing the meta_file and ckpt_file or a model protobuf (.pb) file')
#     parser.add_argument('classifier_filename',
#         help='Classifier model file name as a pickle (.pkl) file. ' +
#         'For training this is the output and for classification this is an input.')
#     parser.add_argument('--use_split_dataset',
#         help='Indicates that the dataset specified by data_dir should be split into a training and test set. ' +
#         'Otherwise a separate test set can be specified using the test_data_dir option.', action='store_true')
#     parser.add_argument('--test_data_dir', type=str,
#         help='Path to the test data directory containing aligned images used for testing.')
#     parser.add_argument('--batch_size', type=int,
#         help='Number of images to process in a batch.', default=90)
#     parser.add_argument('--image_size', type=int,
#         help='Image size (height, width) in pixels.', default=160)
#     parser.add_argument('--seed', type=int,
#         help='Random seed.', default=666)
#     parser.add_argument('--min_nrof_images_per_class', type=int,
#         help='Only include classes with at least this number of images in the dataset', default=20)
#     parser.add_argument('--nrof_train_images_per_class', type=int,
#         help='Use this number of images from each class for training and the rest for testing', default=10)
#
#     return parser.parse_args(argv)
#
# if __name__ == '__main__':
#     main(parse_arguments(sys.argv[1:]))
if __name__ == '__main__':
    start = timer()
    align_mtcnn('DataSet/FaceData/raw', 'DataSet/FaceData/processed')
    trainClassifier('DataSet/FaceData/processed', 'Models/20180402-114759.pb', 'Models/your_model.pkl')
    end = timer()
    print(timedelta(seconds=end - start))