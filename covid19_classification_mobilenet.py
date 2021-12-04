# -*- coding: utf-8 -*-
"""Covid19 Classification Mobilenet.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pR-je-OpM-FARFT_FxaKa0lA1HgejC4b
"""

!pip install keract

from google.colab import drive
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 1.x
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import os, cv2
from tqdm import tqdm
from sklearn.model_selection import StratifiedShuffleSplit
import warnings 
warnings.filterwarnings("ignore")

from keras import optimizers
from keras.models import Sequential, Model, Input
from keras.layers import Dense, Dropout, Flatten, Concatenate
from keras.layers import Conv2D, MaxPooling2D, BatchNormalization
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from keras.applications.inception_v3 import *
from keras.applications.vgg19 import *
from keras.utils import plot_model
from keract import get_activations

import matplotlib.pyplot as plt
def plot_for_class(label):
    nb_rows = 2
    nb_cols = 2
    fig, axs = plt.subplots(nb_rows, nb_cols, figsize=(10, 10))

    n = 0
    for i in range(0, nb_rows):
        for j in range(0, nb_cols):
            axs[i, j].xaxis.set_ticklabels([])
            axs[i, j].yaxis.set_ticklabels([])
            axs[i, j].imshow(images_per_class[label][n])
            n += 1
    plt.show()

x_train = []
x_test = []
y_train = []
label_map = {"pneumonia":0,"corona":1}

from glob import glob
images_per_class = {}
for class_folder_name in os.listdir("/content/drive/My Drive/dataset/train/"):
    class_folder_path = os.path.join("/content/drive/My Drive/dataset/train/", class_folder_name)
    class_label = class_folder_name
    images_per_class[class_label] = []
    for image_path in tqdm(glob(os.path.join(class_folder_path, "*.jpg"))):
        image_bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
        images_per_class[class_label].append(image_bgr)

for key,value in images_per_class.items():
    print("{0} -> {1}".format(key, len(value)))

# for label in  label_map:
#     print(label)
#     plot_for_class(label)

dim = 224

dirs = os.listdir("/content/drive/My Drive/dataset/train/")
for k in range(len(dirs)):    # Directory
    files = os.listdir("/content/drive/My Drive/dataset/train/{}".format(dirs[k]))
    for f in tqdm(range(len(files))):     # Files
        img = cv2.imread('/content/drive/My Drive/dataset/train/{}/{}'.format(dirs[k], files[f]))
        targets = np.zeros(2)
        targets[label_map[dirs[k]]] = 1 
        x_train.append(cv2.resize(img, (dim, dim)))
        y_train.append(targets)

y_train = np.array(y_train, np.uint8)
x_train = np.array(x_train, np.float32)

print(x_train.shape)
print(y_train.shape)

"""### Mobile Net"""

#x_train, x_valid, y_train, y_valid = train_test_split(x_train, y_train, test_size=0.01, random_state=42)
sss = StratifiedShuffleSplit(n_splits=1, test_size=0.10, random_state=42) # Want a balanced split for all the classes
for train_index, test_index in sss.split(x_train, y_train):
    print("Using {} for training and {} for validation".format(len(train_index), len(test_index)))
    x_train, x_valid = x_train[train_index], x_train[test_index]
    y_train, y_valid = y_train[train_index], y_train[test_index]

datagen = ImageDataGenerator(horizontal_flip=True, vertical_flip=True, rescale=1./255)
                                      
weights = os.path.join('', 'weightsinception3.h5')

# from matplotlib import pyplot 

# for X_batch, y_batch in datagen.flow(x_train, y_train, batch_size=9):
# 	# create a grid of 3x3 images
# 	for i in range(0, 9):
# 		pyplot.subplots(330 + 1 + i)
# 		pyplot.imshow(X_batch[i], cmap=pyplot.get_cmap('gray'))
# 	# show the plot
# 	pyplot.show()
# 	break

epochs = 50
learning_rate = 0.0001
batch_size = 32

callbacks = [ EarlyStopping(monitor='val_loss', patience=15, verbose=0), 
              ModelCheckpoint(weights, monitor='val_loss', save_best_only=True, verbose=0),
              ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=10,verbose=0, mode='auto')]

from keras.layers import Dense,GlobalAveragePooling2D
from keras.applications import MobileNet
base_model=MobileNet(input_shape=(dim, dim, 3), weights='imagenet',include_top=False) #imports the mobilenet model and discards the last 1000 neuron layer.
# base_model = InceptionV3(input_shape=(dim, dim, 3), include_top=False, weights='imagenet', pooling='avg') # Average pooling reduces output dimensions
x = base_model.output

x=GlobalAveragePooling2D()(x)
x=Dense(1024,activation='relu')(x) #we add dense layers so that the model can learn more complex functions and classify for better results.
x=Dropout(0.2)(x)
x=Dense(1024,activation='relu')(x) #dense layer 2
x=Dropout(0.2)(x)
x=Dense(512,activation='relu')(x) #dense layer 3
preds = Dense(2, activation='sigmoid')(x)
model=Model(inputs=base_model.input,outputs=preds)
model.summary()

# activations = get_activations(model, x_train, auto_compile=True)
# keract.display_heatmaps(activations, input_image, save=False)

# model.load_weights('/content/drive/My Drive/dataset/Best Model/Mobilenet2.h5')
model.compile(loss='binary_crossentropy', optimizer=optimizers.Adam(lr=learning_rate), metrics=['accuracy'])

history = model.fit_generator(datagen.flow(x_train, y_train, batch_size=batch_size),
                    steps_per_epoch=len(x_train)/batch_size, 
                    validation_data=datagen.flow(x_valid, y_valid, batch_size=batch_size), 
                    validation_steps=len(x_valid)/batch_size,
                    callbacks=callbacks,
                    epochs=epochs)

import matplotlib.pyplot as plt

# Plot training & validation accuracy values
plt.figure(figsize=(20,8))
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper left')
plt.show()

# Plot training & validation loss values
plt.figure(figsize=(20,8))
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper left')
plt.show()

import pandas as pd
results = pd.DataFrame(history.history)
results.sort_values('val_loss', inplace=True)
results
#  results.to_csv("/content/drive/My Drive/dataset/result_mobilenet50_2.csv", index=False)

# import matplotlib.pyplot as plt
# def plot_model(model):
#     plots = [i for i in model.history.history.keys() if i.find('val_') == -1]
#     plt.figure(figsize=(10,10))

#     for i, p in enumerate(plots):
#         plt.subplot(len(plots), 2, i + 1)
#         plt.title(p)
#         plt.plot(model.history.history[p], label=p)
#         plt.plot(model.history.history['val_'+p], label='val_'+p)
#         plt.legend()
#         plt.savefig(f'/content/drive/My Drive/Result Analysis/{i}.jpg')

#     plt.show()
    
# plot_model(model)

# from sklearn.metrics import classification_report, confusion_matrix
# from keras.models import load_model

# model = load_model('/content/drive/My Drive/dataset/Best Model/Mobilenet2.h5')

validation_generator = datagen.flow(x_valid, y_valid)
y_pred = model.predict_generator(validation_generator)
y_pred = np.argmax(y_pred, axis=1)
y_pred

model.evaluate_generator(validation_generator, verbose=1)
