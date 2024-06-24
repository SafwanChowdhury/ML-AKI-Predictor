def DynamicWindowApproach(robot_pose, goal_pose, obstacles, max_speed, max_rotation, max_acceleration, dt):
    while not at goal_pose:
        possible_velocities = calculate_possible_velocities(robot_pose, max_speed, max_acceleration, dt)
        possible_rotations = calculate_possible_rotations(robot_pose, max_rotation, max_acceleration, dt)
        best_trajectory = None
        highest_score = -inf

        for velocity in possible_velocities:
            for rotation in possible_rotations:
                new_pose = predict_new_pose(robot_pose, velocity, rotation, dt)
                distance_to_goal = calculate_distance(new_pose, goal_pose)
                distance_to_closest_obstacle = calculate_distance_to_closest_obstacle(new_pose, obstacles)
                benefit = calculate_benefit(distance_to_goal)
                cost = calculate_cost(distance_to_closest_obstacle)
                score = benefit - cost

                if score > highest_score:
                    highest_score = score
                    best_trajectory = (velocity, rotation)

        setSpeed(best_trajectory.velocity)
        setTheta(best_trajectory.rotation)
        update robot_pose
        sleep(dt) # Wait for the time step to pass before the next cycle
