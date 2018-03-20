import argparse
import time
import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from data import AudioData
from model import ParallelWaveNet

from simple_audio import generate_wave_batch

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('--teacher', type=str, default='teachers/%d' % int(time.time() * 1000), help='Directory where checkpoint and summary is stored')
	parser.add_argument('--student', type=str, default='students/%d' % int(time.time() * 1000), help='Directory where checkpoint and summary is stored')

	parser.add_argument('--train', action='store_true', help='Train student')
	parser.add_argument('--test', action='store_true', help='Test student')

	args = parser.parse_args()

	batch_size = 1
	num_steps = 200000
	print_steps = 100

	last_checkpoint_time = time.time()

	audio_data = AudioData()
	num_samples = audio_data.num_samples
	num_classes = audio_data.classes

	num_samples = 5120
	num_classes = 10
	quantization_channels = 256


	dilations = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512,
              1, 2, 4, 8, 16, 32, 64, 128, 256, 512,
              1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

    # input_size, condition_size, output_size, dilations, filter_width=2, encoder_channels=128, dilation_channels=32, skip_channels=256, 
	# output_channels=256, latent_channels=16, pool_stride=512, name='WaveNetAutoEncoder', learning_rate=0.001):
	#teacher = WaveNetAutoEncoder(input_size=num_samples, condition_size=num_classes, num_mixtures=5, dilations=dilations, pool_stride=512)

	#print('after teacher')

	# input_size, condition_size, output_size, dilations, teacher, num_flows=2, filter_width=2, dilation_channels=32, skip_channels=256, 
	# latent_channels=16, pool_stride=512, name='ParallelWaveNet', learning_rate=0.001
	student = ParallelWaveNet(input_size=num_samples, condition_size=num_classes,
		dilations=dilations, teacher=args.teacher, num_flows=4, pool_stride=512, learning_rate=1e-4)


	with tf.Session(graph=student.graph) as sess:
		sess.run(tf.global_variables_initializer())

		#teacher.load(args.teacher)
		student.load(sess, args.student)

		#print('after load')


		if args.train:
			for global_step in range(num_steps):
				x, y = generate_wave_batch(batch_size, num_samples)

				encoding = student.encode(sess, x, y) 

				num_random_samples = 5

				encoding = np.tile(encoding, [num_random_samples, 1, 1])
				y = np.tile(y, [num_random_samples, 1])

				noise = np.random.logistic(0, 1, [num_random_samples, num_samples])

				#teacher_logits = teacher.
				entropy = student.getEntropy(sess, noise, y, encoding)

				# Train multiple times on different samples
				loss = student.train(sess, noise, y, encoding, x)

				if global_step % print_steps == 0:
					print(global_step, entropy, loss)

					output = student.generate(sess, noise, y, encoding)

					plt.figure(1, figsize=(10, 8))
					plt.subplot(4, 2, 1)
					plt.plot(np.arange(num_samples), x[0])

					plt.subplot(4, 2, 3)
					plt.plot(np.arange(num_samples), noise[0])

					plt.subplot(4, 2, 4)
					plt.plot(np.arange(num_samples), output[0])

					plt.subplot(4, 2, 5)
					plt.plot(np.arange(num_samples), noise[1])

					plt.subplot(4, 2, 6)
					plt.plot(np.arange(num_samples), output[1])

					plt.subplot(4, 2, 7)
					plt.plot(np.arange(num_samples), noise[2])

					plt.subplot(4, 2, 8)
					plt.plot(np.arange(num_samples), output[2])

					if not os.path.isdir(os.path.join(args.student, 'figures')):
						os.makedirs(os.path.join(args.student, 'figures'))

					plt.savefig(os.path.join(args.student, 'figures', '{}.png'.format(global_step)))

					plt.close()



				student.save(sess, args.student, global_step, force=False)
			student.save(sess, args.student, global_step, force=True)


		if args.test:
			for global_step in range(10):
				x, y = generate_wave_batch(batch_size, num_samples)

				encoding = student.encode(sess, x, y) 
				regen = student.reconstruct(sess, x, y)

				noise = np.random.logistic(0, 1, x.shape)
				entropy = student.getEntropy(sess, noise, y, encoding)
				output = student.generate(sess, noise, y, encoding)

				#loss = student.train(sess, noise, y, encoding)

				print('Entropy', entropy)
				#print('loss', loss)


				plt.figure(1)
				plt.subplot(221)

				plt.plot(np.arange(num_samples), x[0])	

				plt.subplot(222)
				plt.plot(np.arange(num_samples), regen[0])

				
				plt.subplot(223)
				plt.plot(np.arange(num_samples), noise[0])
				
				plt.subplot(224)
				plt.plot(np.arange(num_samples), output[0])

				plt.show()
