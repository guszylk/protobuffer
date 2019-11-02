import os
from functools import partial
from os.path import join

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow.python.platform import tf_logging as logging

import data_utils
import tensorflow_model

import matplotlib.image as mpimg

num_classes = 10
labels = {"airplane.png": 0, "automobile.png": 1, "bird.png": 2, "cat.png": 3, "deer.png": 4, "dog.png": 5, "frog.png": 6, "horse.png": 7, "ship.png": 8, "truck.png": 9}
class_maping = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


# Environment variable containing port to launch TensorBoard on, set by TonY.
# based on https://androidkt.com/train-keras-model-with-tensorflow-estimators-and-datasets-api/
TB_PORT_ENV_VAR = 'TB_PORT'
tf.flags.DEFINE_string('tfrecord_path'      , '/home/gus/Descargas/cifar/tfrecords', 'The base path where the tfrecords are stored, hdfs://namenode is valid protocol')
tf.flags.DEFINE_string('tftraining_file'    , 'train.tfrecords', 'The filename with the training data is stored as tfrecods')
tf.flags.DEFINE_string('tftesting_file'     , 'test.tfrecords', 'The filename with the test data is stored as tfrecods')
tf.flags.DEFINE_string('estimator_path'     , 'kkt', 'The working path used by the estimator to process the data')
tf.flags.DEFINE_string('export_model_path'  , './export', 'The path where the model is exported as .pb file')
tf.flags.DEFINE_boolean('plot_enabeld'  , False, 'If we want to plot the accuracy of the model, only for local training')
#tf.flags.DEFINE_integer("batch_size", 64, "The batch size per step.")
FLAGS = tf.flags.FLAGS

def getFileList(dir):
    x = []
    y = []
    for f in os.listdir(dir):
        path = join(dir, f)
        if os.path.isfile(path):
            y.append(labels.get(f.split("_")[1]))
            x.append(path)
    return x, y


def prediction_data():
    bas_dir = "/home/gus/Descargas/cifar"
    predict_dir = join(bas_dir, "predict")
    predict_image, true_labels = getFileList(predict_dir)
    return predict_image[1:45], true_labels[1:45]


def _parse_function(filename):
    image_string = tf.read_file(filename)
    image_decoded = tf.image.decode_jpeg(image_string, channels=3)
    image_decoded = tf.image.convert_image_dtype(image_decoded, tf.float32)
    image_decoded = image_decoded
    image_decoded.set_shape([32, 32, 3])
    return {"input_1": image_decoded}


def predict_input_fn(image_path):
    img_filenames = tf.constant(image_path)
    dataset = tf.data.Dataset.from_tensor_slices(img_filenames)
    dataset = dataset.map(_parse_function)
    dataset = dataset.repeat(1)
    dataset = dataset.batch(32)
    iterator = dataset.make_one_shot_iterator()
    image = iterator.get_next()
    return image

def serving_input_receiver_fn():
    input_ph = tf.placeholder(tf.string, shape=[None], name='image_binary')
    images = tf.map_fn(partial(tf.image.decode_image, channels=1), input_ph, dtype=tf.uint8)
    images = tf.cast(images, tf.float32) / 255.
    images.set_shape([None, 32, 32, 3])
    return tf.estimator.export.ServingInputReceiver({model_input_name: images}, {'bytes': input_ph})

def train_and_evaluate():
    tfrecord_path = FLAGS.tfrecord_path #"/home/gus/Descargas/cifar/tfrecords"
    tftraining_file = FLAGS.tftraining_file #"train.tfrecords"
    tftesting_file = FLAGS.tftesting_file #"test.tfrecords"
    estimator_path = FLAGS.estimator_path #"kkt"
    export_model_path = FLAGS.export_model_path #"./export"
    plot_enabeld = FLAGS.plot_enabeld #False
    
    train_data = os.path.join(tfrecord_path, tftraining_file)
    test_data = os.path.join(tfrecord_path, tftesting_file)
#     model = tensorflow_model.cnn_model()
#     model.compile(optimizer=tf.keras.optimizers.Adam(),loss=tf.keras.losses.categorical_crossentropy,metrics=['accuracy'])
#     cifar_est = tf.keras.estimator.model_to_estimator(keras_model=model, model_dir="kkt")
    cifar_est = tensorflow_model.build_estimator(tensorflow_model.cnn_model(),estimator_path)
    
    train_input = lambda: data_utils.dataset_input_fn(train_data, None)
    cifar_est.train(input_fn=train_input, steps=7000)
    
    test_input = lambda: data_utils.dataset_input_fn(test_data, 1)
    res = cifar_est.evaluate(input_fn=test_input, steps=1)
    print(res)
    model_input_name = model.input_names[0]
    export_path = cifar_est.export_savedmodel(export_model_path, serving_input_receiver_fn=serving_input_receiver_fn)
    predict_image, true_label = prediction_data()
    predict_result = list(cifar_est.predict(input_fn=lambda: predict_input_fn(predict_image)))
    
    if(plot_enabeld):
        pos = 1
        for img, lbl, predict_lbl in zip(predict_image, true_label, predict_result):
            output = np.argmax(predict_lbl.get('output'), axis=None)
            plt.subplot(4, 11, pos)
            img = mpimg.imread(img)
            plt.imshow(img)
            plt.axis('off')
            if output == lbl:
                plt.title(class_maping[output])
            else:
                plt.title(class_maping[output] + "/" + class_maping[lbl], color='#ff0000')
            pos += 1
        plt.show()

if __name__ == '__main__':
    #tf.logging.set_verbosity(args.verbosity)
    logging.set_verbosity(logging.INFO)
    logging.log(logging.INFO, "Tensorflow version " + tf.__version__)
    train_and_evaluate()