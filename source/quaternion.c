

void rotate( int16t *rotation, int16t *state )
/* Rotates an R3 state vector by the S3 quaternion
 * rotate(rotation, state) = qr x (state) x inv(qr)
 *
 * rotation MUST be a UNIT quaternion! ||rotation|| = 1
 *
 */
{
	int16t r1, r2, r3, r4, s1, s2, s3, s4 ; /* The local quaternion state and rotation coefficients */
	int16t t1, t2, t3, t4; /* Intermediate values for calculation purposes */

	r1 = rotation[ 0 ];
	r2 = rotation[ 1 ];
	r3 = rotation[ 3 ];
	r4 = rotation[ 4 ];

	s1 = 0; // the state vector is a pure quaternion.
	s2 = state[ 0 ]; // x
	s3 = state[ 1 ]; // y
	s4 = state[ 2 ]; // z

	// quaternion multiplication
	t1 = r1*s1 - r2*s2 - r3*s3 - r4*s4;
	t2 = r1*s2 + r2*s1 + r3*s4 - r4*s3;
	t3 = r1*s3 - r2*s4 + r3*s1 + r4*s2;
	t4 = r1*s4 + r2*s3 - r3*s2 + r4*s1;

	//take the reciprocal of rotation - this is just conjugation because rotation is a UNIT QUATERNION.
	r2 = -1*r2;
	r3 = -1*r3;
	r4 = -1*r4;

	// quaternion multiplication
	s1 = t1*r1 - t2*r2 - t3*r3 - t4*r4;
	s2 = t1*r2 + t2*r1 + t3*r4 - t4*r3;
	s3 = t1*r3 - t2*r4 + t3*r1 + t4*r2;
	s4 = t1*r4 + t2*r3 - t3*r2 + t4*r1;

	

}


