content = """// Server component wrapper
import DeviceDetailClient from './DeviceDetailClient';

export function generateStaticParams() {
  return [
    { id: '1' }, { id: '2' }, { id: '3' }, { id: '4' }, { id: '5' }, { id: '6' }
  ];
}

export default function DeviceDetailPage({ params }: { params: { id: string } }) {
  return <DeviceDetailClient deviceId={params.id} />;
}
"""

with open('/home/erik-ross/projects/vigil-home/dashboard/src/app/devices/[id]/page.tsx', 'w') as f:
    f.write(content)
print('Done')
