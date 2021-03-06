"""
Unit test for EC2 subnet.
"""

import unittest
import mock

from treadmill.infra.subnet import Subnet


class SubnetTest(unittest.TestCase):

    @mock.patch('treadmill.infra.connection.Connection')
    def test_init(self, ConnectionMock):
        conn_mock = ConnectionMock()
        subnet = Subnet(
            id=1,
            vpc_id='vpc-id',
            metadata={
                'Tags': [{
                    'Key': 'Name',
                    'Value': 'goo'
                }]
            }
        )

        self.assertEquals(subnet.vpc_id, 'vpc-id')
        self.assertEquals(subnet.name, 'goo')
        self.assertEquals(subnet.ec2_conn, conn_mock)

    @mock.patch('treadmill.infra.connection.Connection')
    def test_create_tags(self, ConnectionMock):
        conn_mock = ConnectionMock()
        conn_mock.create_tags = mock.Mock()

        subnet = Subnet(
            name='foo',
            id='1',
            vpc_id='vpc-id'
        )
        subnet.create_tags()

        conn_mock.create_tags.assert_called_once_with(
            Resources=['1'],
            Tags=[{
                'Key': 'Name',
                'Value': 'foo'
            }]
        )

    @mock.patch('treadmill.infra.connection.Connection')
    def test_create(self, ConnectionMock):
        ConnectionMock.context.region_name = 'us-east-1'
        conn_mock = ConnectionMock()
        subnet_json_mock = {
            'Subnet': {
                'SubnetId': '1'
            }
        }
        conn_mock.create_subnet = mock.Mock(return_value=subnet_json_mock)
        conn_mock.create_route_table = mock.Mock(return_value={
            'RouteTable': {'RouteTableId': 'route-table-id'}
        })

        _subnet = Subnet.create(
            cidr_block='172.23.0.0/24',
            vpc_id='vpc-id',
            name='foo',
            gateway_id='gateway-id'
        )
        self.assertEqual(_subnet.id, '1')
        self.assertEqual(_subnet.name, 'foo')
        self.assertEqual(_subnet.metadata, subnet_json_mock)
        conn_mock.create_subnet.assert_called_once_with(
            VpcId='vpc-id',
            CidrBlock='172.23.0.0/24',
            AvailabilityZone='us-east-1a'
        )
        conn_mock.create_tags.assert_called_once_with(
            Resources=['1'],
            Tags=[{
                'Key': 'Name',
                'Value': 'foo'
            }]
        )
        conn_mock.create_route_table.assert_called_once_with(
            VpcId='vpc-id'
        )
        conn_mock.create_route.assert_called_once_with(
            RouteTableId='route-table-id',
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId='gateway-id'
        )
        conn_mock.associate_route_table.assert_called_once_with(
            RouteTableId='route-table-id',
            SubnetId='1',
        )

    @mock.patch('treadmill.infra.connection.Connection')
    def test_refresh(self, ConnectionMock):
        conn_mock = ConnectionMock()
        subnet_json_mock = {
            'VpcId': 'vpc-id',
            'Foo': 'bar'
        }
        conn_mock.describe_subnets = mock.Mock(return_value={
            'Subnets': [subnet_json_mock]
        })

        _subnet = Subnet(id='subnet-id', vpc_id=None, metadata=None)
        _subnet.refresh()

        self.assertEqual(_subnet.vpc_id, 'vpc-id')
        self.assertEqual(_subnet.metadata, subnet_json_mock)

    @mock.patch.object(Subnet, 'refresh')
    @mock.patch.object(Subnet, 'get_instances')
    @mock.patch('treadmill.infra.connection.Connection', mock.Mock())
    def test_show(self, get_instances_mock, refresh_mock):
        _subnet = Subnet(id='subnet-id',
                         vpc_id='vpc-id',
                         metadata=None)
        _subnet.instances = None

        result = _subnet.show()

        self.assertEqual(
            result,
            {
                'VpcId': 'vpc-id',
                'SubnetId': 'subnet-id',
                'Instances': None
            }
        )

        get_instances_mock.assert_called_once_with(refresh=True, role=None)
        refresh_mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
