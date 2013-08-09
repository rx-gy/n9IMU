def q_multiply( q1, q2 ):
	q3 = [0,0,0,0]
	q3[0] = q1[0] * q2[0] - q1[1] * q2[1] - q1[2] * q2[2] - q1[3] * q2[3]
	q3[1] = q1[0] * q2[1] + q1[1] * q2[0] + q1[2] * q2[3] - q1[3] * q2[2]
	q3[2] = q1[0] * q2[2] - q1[1] * q2[3] + q1[2] * q2[0] + q1[3] * q2[1]
	q3[3] = q1[0] * q2[3] + q1[1] * q2[2] - q1[2] * q2[1] + q1[3] * q2[0]

	return q3

def q_conj( q1 ):
	q2 = [0,0,0,0]
	q2[0] = q1[0]
	q2[1] = q1[1] * -1
	q2[2] = q1[2] * -1
	q2[3] = q1[3] * -1

	return q2
def rotate( rotation, state ):
	""" note rotation and state are both quaternions, rotation MUST be a unit quaternion and state should be a
	pure quaternion (real part = 0).
	"""
	q1 = q_multiply( rotation, state )
	r = q_conj( rotation )
	q2 = q_multiply( q1, r )
	return q2

