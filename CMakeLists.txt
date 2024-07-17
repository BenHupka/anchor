cmake_minimum_required(VERSION 3.5)
project(anchor)
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

install(PROGRAMS
  nodes/anker_node.py
  nodes/anker_node_2.py
  nodes/anker_mqtt_final.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
