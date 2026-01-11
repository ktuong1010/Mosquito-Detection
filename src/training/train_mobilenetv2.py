import sys
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, CSVLogger
from tensorflow.keras.regularizers import l2
import matplotlib.pyplot as plt
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def preprocess_mobilenetv2(image):
    image = tf.cast(image, tf.float32)
    image = (image / 127.5) - 1.0
    return image


class MobileNetV2Trainer:
    def __init__(
        self,
        data_dir: Path,
        model_output: Path,
        input_size: tuple = (224, 224),
        num_classes: int = None,  # Auto-detect from dataset
        batch_size: int = 32,
        epochs: int = 30
    ):
        self.data_dir = Path(data_dir)
        self.model_output = Path(model_output)
        self.input_size = input_size
        self.num_classes = num_classes
        self.batch_size = batch_size
        self.epochs = epochs
        
        self.model_output.parent.mkdir(parents=True, exist_ok=True)
        
        self.base_model = None
        self.model = None
        self.history = None
    
    def create_data_generators(self):
        train_datagen = ImageDataGenerator(
            preprocessing_function=preprocess_mobilenetv2,
            rotation_range=20,
            width_shift_range=0.15,
            height_shift_range=0.15,
            shear_range=0.15,
            zoom_range=0.2,
            horizontal_flip=True,
            vertical_flip=False,
            fill_mode='nearest',
            brightness_range=[0.7, 1.3],
            validation_split=0.0
        )
        
        val_datagen = ImageDataGenerator(
            preprocessing_function=preprocess_mobilenetv2
        )
        
        train_dir = self.data_dir / "train"
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=self.input_size[::-1],
            batch_size=self.batch_size,
            class_mode='categorical',
            shuffle=True
        )
        
        val_dir = self.data_dir / "val"
        val_generator = val_datagen.flow_from_directory(
            val_dir,
            target_size=self.input_size[::-1],
            batch_size=self.batch_size,
            class_mode='categorical',
            shuffle=False
        )
        
        logger.info(f"Training samples: {train_generator.samples}")
        logger.info(f"Validation samples: {val_generator.samples}")
        logger.info(f"Classes: {train_generator.class_indices}")
        
        # Auto-detect number of classes from dataset
        detected_num_classes = len(train_generator.class_indices)
        if self.num_classes is None:
            self.num_classes = detected_num_classes
            logger.info(f"Auto-detected {self.num_classes} classes from dataset")
        elif self.num_classes != detected_num_classes:
            logger.warning(f"Config num_classes ({self.num_classes}) != detected classes ({detected_num_classes})")
            logger.warning(f"Using detected number: {detected_num_classes}")
            self.num_classes = detected_num_classes
        
        return train_generator, val_generator
    
    def build_model(self):
        from tensorflow.keras.applications import MobileNetV2
        
        base_model = MobileNetV2(
            input_shape=(self.input_size[1], self.input_size[0], 3),
            include_top=False,
            weights='imagenet',
            alpha=1.0
        )
        
        base_model.trainable = False
        
        inputs = keras.Input(shape=(224, 224, 3))
        x = base_model(inputs, training=False)
        x = layers.GlobalAveragePooling2D()(x)
        
        x = layers.Dropout(0.6)(x)
        
        x = layers.Dense(
            128,
            activation='relu',
            kernel_regularizer=l2(0.001),
            bias_regularizer=l2(0.001)
        )(x)
        x = layers.Dropout(0.5)(x)
        
        outputs = layers.Dense(
            self.num_classes,
            activation='softmax',
            kernel_regularizer=l2(0.001)
        )(x)
        
        model = models.Model(inputs, outputs)
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'top_k_categorical_accuracy']
        )
        
        self.base_model = base_model
        self.model = model
        
        logger.info("MobileNetV2 model built successfully")
        logger.info(f"Total parameters: {model.count_params():,}")
        
        return model
    
    def train(self, train_generator, val_generator):
        callbacks = [
            ModelCheckpoint(
                filepath=str(self.model_output.parent / "best_model.h5"),
                monitor='val_accuracy',
                save_best_only=True,
                mode='max',
                verbose=1
            ),
            
            EarlyStopping(
                monitor='val_loss',
                patience=7,
                restore_best_weights=True,
                verbose=1,
                mode='min'
            ),
            
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                min_lr=1e-7,
                verbose=1,
                mode='min'
            ),
            
            CSVLogger(
                filename=str(self.model_output.parent / "training_history.csv"),
                append=False
            )
        ]
        
        logger.info("=" * 80)
        logger.info("Phase 1: Training top layers (base model frozen)")
        logger.info("=" * 80)
        
        history1 = self.model.fit(
            train_generator,
            epochs=self.epochs,
            validation_data=val_generator,
            callbacks=callbacks,
            verbose=1
        )
        
        logger.info("=" * 80)
        logger.info("Training completed (Phase 1 only - frozen base for better generalization)")
        logger.info("=" * 80)
        
        self.history = {
            'loss': history1.history['loss'],
            'val_loss': history1.history['val_loss'],
            'accuracy': history1.history['accuracy'],
            'val_accuracy': history1.history['val_accuracy']
        }
        
        self.model.save(str(self.model_output))
        logger.info(f"Model saved to: {self.model_output}")
        
        return self.history
    
    def convert_to_tflite(self, output_path: Path = None):
        if output_path is None:
            output_path = self.model_output.parent / "model.tflite"
        
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        tflite_model = converter.convert()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        logger.info(f"TFLite model saved to: {output_path}")
        logger.info(f"Model size: {len(tflite_model) / 1024 / 1024:.2f} MB")
        
        return output_path
    
    def plot_training_history(self, output_path: Path = None):
        if output_path is None:
            output_path = self.model_output.parent / "training_history.png"
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        ax1.plot(self.history['loss'], label='Training Loss')
        ax1.plot(self.history['val_loss'], label='Validation Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.set_title('Model Loss')
        ax1.legend()
        ax1.grid(True)
        
        ax2.plot(self.history['accuracy'], label='Training Accuracy')
        ax2.plot(self.history['val_accuracy'], label='Validation Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy')
        ax2.set_title('Model Accuracy')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Training history plot saved to: {output_path}")
        plt.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Train MobileNetV2 model for Aedes vs Culex classification")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "dataset" / "processed_edgeimpulse", help="Path to processed dataset")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "models" / "mobilenetv2.h5", help="Output model path")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--epochs", type=int, default=30, help="Number of epochs")
    parser.add_argument("--convert-tflite", action="store_true", help="Convert to TFLite after training")
    
    args = parser.parse_args()
    
    if not args.data_dir.exists():
        logger.error(f"Data directory not found: {args.data_dir}")
        return 1
    
    train_dir = args.data_dir / "train"
    if not train_dir.exists():
        logger.error(f"Training directory not found: {train_dir}")
        return 1
    
    trainer = MobileNetV2Trainer(
        data_dir=args.data_dir,
        model_output=args.output,
        batch_size=args.batch_size,
        epochs=args.epochs
    )
    
    logger.info("Creating data generators...")
    train_gen, val_gen = trainer.create_data_generators()
    
    logger.info("Building model...")
    trainer.build_model()
    
    logger.info("Starting training...")
    logger.info("Using MobileNetV2 with regularization to prevent overfitting")
    history = trainer.train(train_gen, val_gen)
    
    trainer.plot_training_history()
    
    if args.convert_tflite:
        logger.info("Converting to TFLite...")
        trainer.convert_to_tflite()
    
    final_val_acc = max(history['val_accuracy'])
    final_train_acc = max(history['accuracy'])
    logger.info("=" * 80)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Best validation accuracy: {final_val_acc:.2%}")
    logger.info(f"Best training accuracy: {final_train_acc:.2%}")
    logger.info(f"Overfitting gap: {(final_train_acc - final_val_acc) * 100:.2f}%")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

