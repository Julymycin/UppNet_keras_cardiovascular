import tensorflow as tf
import keras

from keras.layers import Input, Conv2D, MaxPooling2D, Dropout, BatchNormalization, Conv2DTranspose, concatenate, \
    Activation, UpSampling2D, Cropping2D, Reshape, Permute
from keras.regularizers import l2
from keras.models import Model
from keras.optimizers import Adam

act = 'relu'
# channels last or first
global ch_axis
if keras.backend.image_dim_ordering() == 'tf':  # channels_last
    ch_axis = -1
else:
    ch_axis = 1


# Conv2D standard unit
def conv2d(input_layer, block, nb_filter, dropout_rate=0.25, kernel_size=(3, 3), bn_axis=ch_axis):
    x = Conv2D(nb_filter, kernel_size, kernel_initializer='he_normal', kernel_regularizer=l2(1e-4),
               padding='same', name='conv' + str(block) + '_1')(input_layer)
    x = BatchNormalization(axis=bn_axis, name='bn' + str(block) + '_1')(x)
    x = Activation(act)(x)
    x = Dropout(dropout_rate, name='dp' + str(block) + '_1')(x)
    x = Conv2D(nb_filter, kernel_size, kernel_initializer='he_normal', kernel_regularizer=l2(1e-4),
               padding='same', name='conv' + str(block) + '_2')(x)
    x = BatchNormalization(axis=bn_axis, name='bn' + str(block) + '_2')(x)
    x = Activation(act)(x)
    x = Dropout(dropout_rate, name='dp' + str(block) + '_2')(x)

    return x


def upp_model(img_rows, img_cols, nb_channel, nb_class, deep_supervision=False):
    nb_filter = [32, 64, 128, 256, 512]
    if ch_axis == -1:
        inputs = Input(shape=(img_rows, img_cols, nb_channel), name='main_input')
    else:
        inputs = Input(shape=(nb_channel, img_rows, img_cols), name='main_input')

    conv1_1 = conv2d(inputs, block='11', nb_filter=nb_filter[0])
    pool1 = MaxPooling2D((2, 2), strides=(2, 2), name='pool1')(conv1_1)

    conv2_1 = conv2d(pool1, block='21', nb_filter=nb_filter[1])
    pool2 = MaxPooling2D((2, 2), strides=(2, 2), name='pool2')(conv2_1)

    up1_2 = Conv2DTranspose(nb_filter[0], (2, 2), strides=(2, 2), name='up12', padding='same')(conv2_1)
    conv1_2 = concatenate([up1_2, conv1_1], name='merge12', axis=ch_axis)
    conv1_2 = conv2d(conv1_2, block='12', nb_filter=nb_filter[0])

    conv3_1 = conv2d(pool2, block='31', nb_filter=nb_filter[2])
    pool3 = MaxPooling2D((2, 2), strides=(2, 2), name='pool3')(conv3_1)

    up2_2 = Conv2DTranspose(nb_filter[1], (2, 2), strides=(2, 2), name='up22', padding='same')(conv3_1)
    conv2_2 = concatenate([up2_2, conv2_1], name='merge22', axis=ch_axis)
    conv2_2 = conv2d(conv2_2, block='22', nb_filter=nb_filter[1])

    up1_3 = Conv2DTranspose(nb_filter[0], (2, 2), strides=(2, 2), name='up13', padding='same')(conv2_2)
    conv1_3 = concatenate([up1_3, conv1_1, conv1_2], name='merge13', axis=ch_axis)
    conv1_3 = conv2d(conv1_3, block='13', nb_filter=nb_filter[0])

    conv4_1 = conv2d(pool3, block='41', nb_filter=nb_filter[3])
    pool4 = MaxPooling2D((2, 2), strides=(2, 2), name='pool4')(conv4_1)

    up3_2 = Conv2DTranspose(nb_filter[2], (2, 2), strides=(2, 2), name='up32', padding='same')(conv4_1)
    conv3_2 = concatenate([up3_2, conv3_1], name='merge32', axis=ch_axis)
    conv3_2 = conv2d(conv3_2, block='32', nb_filter=nb_filter[2])

    up2_3 = Conv2DTranspose(nb_filter[1], (2, 2), strides=(2, 2), name='up23', padding='same')(conv3_2)
    conv2_3 = concatenate([up2_3, conv2_1, conv2_2], name='merge23', axis=ch_axis)
    conv2_3 = conv2d(conv2_3, block='23', nb_filter=nb_filter[1])

    up1_4 = Conv2DTranspose(nb_filter[0], (2, 2), strides=(2, 2), name='up14', padding='same')(conv2_3)
    conv1_4 = concatenate([up1_4, conv1_1, conv1_2, conv1_3], name='merge14', axis=ch_axis)
    conv1_4 = conv2d(conv1_4, block='14', nb_filter=nb_filter[0])

    conv5_1 = conv2d(pool4, block='5', nb_filter=nb_filter[4])

    up4_2 = Conv2DTranspose(nb_filter[3], (2, 2), strides=(2, 2), name='up42', padding='same')(conv5_1)
    conv4_2 = concatenate([up4_2, conv4_1], name='merge42', axis=ch_axis)
    conv4_2 = conv2d(conv4_2, block='42', nb_filter=nb_filter[3])

    up3_3 = Conv2DTranspose(nb_filter[2], (2, 2), strides=(2, 2), name='up33', padding='same')(conv4_2)
    conv3_3 = concatenate([up3_3, conv3_1, conv3_2], name='merge33', axis=ch_axis)
    conv3_3 = conv2d(conv3_3, block='33', nb_filter=nb_filter[2])

    up2_4 = Conv2DTranspose(nb_filter[1], (2, 2), strides=(2, 2), name='up24', padding='same')(conv3_3)
    conv2_4 = concatenate([up2_4, conv2_1, conv2_2, conv2_3], name='merge24', axis=ch_axis)
    conv2_4 = conv2d(conv2_4, block='24', nb_filter=nb_filter[1])

    up1_5 = Conv2DTranspose(nb_filter[0], (2, 2), strides=(2, 2), name='up15', padding='same')(conv2_4)
    conv1_5 = concatenate([up1_5, conv1_1, conv1_2, conv1_3, conv1_4], name='merge15', axis=ch_axis)
    conv1_5 = conv2d(conv1_5, block='15', nb_filter=nb_filter[0])

    nestnet_output_1 = Conv2D(nb_class, (1, 1), activation='softmax', name='output_1', kernel_initializer='he_normal',
                              padding='same', kernel_regularizer=l2(1e-4))(conv1_2)
    nestnet_output_2 = Conv2D(nb_class, (1, 1), activation='softmax', name='output_2', kernel_initializer='he_normal',
                              padding='same', kernel_regularizer=l2(1e-4))(conv1_3)
    nestnet_output_3 = Conv2D(nb_class, (1, 1), activation='softmax', name='output_3', kernel_initializer='he_normal',
                              padding='same', kernel_regularizer=l2(1e-4))(conv1_4)
    nestnet_output_4 = Conv2D(nb_class, (1, 1), activation='softmax', name='output_4', kernel_initializer='he_normal',
                              padding='same', kernel_regularizer=l2(1e-4))(conv1_5)

    if deep_supervision:
        model = Model(inputs=inputs, outputs=[nestnet_output_1,
                                              nestnet_output_2,
                                              nestnet_output_3,
                                              nestnet_output_4])
    else:
        model = Model(inputs=inputs, outputs=[nestnet_output_4])
    model.compile(optimizer=Adam(lr=1.0e-4), loss='categorical_crossentropy', metrics=['accuracy'])
    model.summary()

    return model


def get_crop_shape(target, refer):
    # width, the 3rd dimension
    print([target.get_shape()[0].value, target.get_shape()[1].value, target.get_shape()[2].value,
           target.get_shape()[3].value])
    print([refer.get_shape()[0].value, refer.get_shape()[1].value, refer.get_shape()[2].value,
           refer.get_shape()[3].value])
    cw = (target.get_shape()[2] - refer.get_shape()[2]).value
    assert (cw >= 0)
    if cw % 2 != 0:
        cw1, cw2 = int(cw / 2), int(cw / 2) + 1
    else:
        cw1, cw2 = int(cw / 2), int(cw / 2)
    # height, the 2nd dimension
    ch = (target.get_shape()[1] - refer.get_shape()[1]).value
    assert (ch >= 0)
    if ch % 2 != 0:
        ch1, ch2 = int(ch / 2), int(ch / 2) + 1
    else:
        ch1, ch2 = int(ch / 2), int(ch / 2)

    return (ch1, ch2), (cw1, cw2)


def unet4_model(img_rows, img_cols, nb_channel, nb_class):
    inputs = Input(shape=(img_rows, img_cols, nb_channel))
    concat_axis = -1
    k = 64
    # Block 1
    conv1 = Conv2D(k, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(inputs)
    conv1 = Conv2D(k, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(conv1)
    pool1 = MaxPooling2D((2, 2), strides=(2, 2), name='block1_pool')(conv1)

    # Block 2
    conv2 = Conv2D(k * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(pool1)
    conv2 = Conv2D(k * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(conv2)
    pool2 = MaxPooling2D((2, 2), strides=(2, 2), name='block2_pool')(conv2)

    # Block 3
    conv3 = Conv2D(k * 2 * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(pool2)
    conv3 = Conv2D(k * 2 * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(conv3)
    pool3 = MaxPooling2D((2, 2), strides=(2, 2), name='block3_pool')(conv3)

    # Block 4
    conv4 = Conv2D(k * 2 * 2 * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(pool3)
    conv4 = Conv2D(k * 2 * 2 * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(conv4)

    # Block 5
    up_conv4 = UpSampling2D(size=(2, 2), data_format="channels_last")(conv4)
    ch, cw = get_crop_shape(conv3, up_conv4)
    crop_conv3 = Cropping2D(cropping=(ch, cw), data_format="channels_last")(conv3)
    up5 = concatenate([up_conv4, crop_conv3], axis=concat_axis)
    conv5 = Conv2D(k * 2 * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(up5)
    conv5 = Conv2D(k * 2 * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(conv5)

    # Block 6
    up_conv5 = UpSampling2D(size=(2, 2), data_format="channels_last")(conv5)
    ch, cw = get_crop_shape(conv2, up_conv5)
    crop_conv2 = Cropping2D(cropping=(ch, cw), data_format="channels_last")(conv2)
    up6 = concatenate([up_conv5, crop_conv2], axis=concat_axis)
    conv6 = Conv2D(k * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(up6)
    conv6 = Conv2D(k * 2, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(conv6)

    # Block 7
    up_conv6 = UpSampling2D(size=(2, 2), data_format="channels_last")(conv6)
    ch, cw = get_crop_shape(conv1, up_conv6)
    crop_conv1 = Cropping2D(cropping=(ch, cw), data_format="channels_last")(conv1)
    up7 = concatenate([up_conv6, crop_conv1], axis=concat_axis)
    conv7 = Conv2D(k, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(up7)
    conv7 = Conv2D(k, (3, 3), activation='relu', padding='same', kernel_initializer='he_normal')(conv7)
    conv8 = Conv2D(nb_class, (1, 1), activation='softmax', padding='same', kernel_initializer='he_normal')(conv7)

    # reshape = Reshape((nb_class, img_cols * img_rows), input_shape=(nb_class, img_cols, img_rows))(conv8)
    # reshape = Permute((2, 1))(reshape)
    # activation = Activation('softmax')(reshape)

    model = Model(inputs=inputs, outputs=conv8)
    model.compile(optimizer=Adam(lr=1.0e-4), loss='categorical_crossentropy', metrics=['accuracy'])
    model.summary()

    return model


if __name__ == '__main__':
    # model = upp_model(256, 256, 3, 2, True)
    model = unet4_model(480, 480, 3, 5)
