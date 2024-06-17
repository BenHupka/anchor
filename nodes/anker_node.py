#!/usr/bin/env python3
"""
Test für Anker Node - aktuell mqtt Version für Setup von Cyber Physical Systems genutzt
"""
import rclpy
from hippo_msgs.msg import AhoiPacket
from rclpy.node import Node
from ahoi.modem.modem import Modem
from rclpy.duration import Duration


class anker_node(Node):

    def __init__(self):
        super().__init__(node_name='anker_node')

        self.id = 0  # TODO Anker-ID anpassen

        self.myModem = Modem()
        self.myModem.connect("/dev/ttyUSB0")  # TODO port anpassen
        self.myModem.setTxEcho(
            True)  # übertragene und empfangene Pakete in Terminal echoen
        self.myModem.setRxEcho(True)

        self.myModem.addRxCallback(self.anchorCallback)
        self.myModem.receive(thread=True)

        # TODO subscribe to anchor pose, add on_anchor_pose function

        self.sent_packets_pub = self.create_publisher(msg_type=AhoiPacket,
                                                      topic='sent_packets',
                                                      qos_profile=1)

        self.received_packets_pub = self.create_publisher(
            msg_type=AhoiPacket, topic='received_packets', qos_profile=1)

    def anchorCallback(self, pkt):
        if pkt.header.dst == self.id:
            src = pkt.header.src
            dst = pkt.header.dst
            type = pkt.header.type
            status = pkt.header.status
            self.publish_received_packets(src, dst, type, status)
            self.get_logger().info(
                f'received: src {src}, dst {dst}, type {type}, status {status}')

        # check if initial position is requested (Pakettyp 0x7C)
        if pkt.header.type == 0x7C and pkt.header.dst == self.id:
            position_x = 1499
            position_y = 1499
            position = position_x.to_bytes(2, 'big',
                                           signed=True) + position_y.to_bytes(
                                               2, 'big', signed=True)
            self.myModem.send(
                dst=9, payload=position, status=0, src=self.id,
                type=0x7B)  # initiale Ankerposition übertragen (Pakettyp 0x7B)
            self.publish_sent_packets(self.id, 9, 123, 0)
            self.get_logger().info(f"send initial position")

        # check if position is requested (Pakettyp 0x7E)
        if pkt.header.type == 0x7E and pkt.header.dst == self.id:
            self.get_clock().sleep_for(
                Duration(seconds=1))  # wait before sending position
            position_x = 1500
            position_y = 1500
            position = position_x.to_bytes(2, 'big',
                                           signed=True) + position_y.to_bytes(
                                               2, 'big', signed=True)
            self.myModem.send(
                dst=9, payload=position, status=0, src=self.id,
                type=0x7D)  # Ankerposition übertragen (Pakettyp 0x7D)
            self.publish_sent_packets(self.id, 9, 125, 0)
            self.get_logger().info(f"send position")

    def publish_sent_packets(self, src, dst, type, status):
        msg = AhoiPacket()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.src = src
        msg.dst = dst
        msg.type = type
        msg.status = status
        self.sent_packets_pub.publish(msg)

    def publish_received_packets(self, src, dst, type, status):
        msg = AhoiPacket()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.src = src
        msg.dst = dst
        msg.type = type
        msg.status = status
        self.received_packets_pub.publish(msg)


def main():
    rclpy.init()
    node = anker_node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
