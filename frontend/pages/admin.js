import { useState, useEffect } from 'react';
import io from 'socket.io-client';

const socket = io(process.env.NEXT_PUBLIC_API_URL);

export default function AdminDashboard({ initialOrders }) {
    const [orders, setOrders] = useState(initialOrders);

    useEffect(() => {
        socket.on('new_order', (newOrder) => {
            setOrders(prevOrders => [newOrder, ...prevOrders]);
            // Optional: Play a sound
            new Audio('/notification.mp3').play(); 
        });

        socket.on('order_status_update', (updatedOrder) => {
            setOrders(prevOrders => 
                prevOrders.map(o => o.id === updatedOrder.id ? updatedOrder : o)
            );
        });

        return () => {
            socket.off('new_order');
            socket.off('order_status_update');
        };
    }, []);

    const updateStatus = async (id, status) => {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/orders/${id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
        });
    };
    
    const preparingOrders = orders.filter(o => o.status === 'Preparing');
    const readyOrders = orders.filter(o => o.status === 'Ready');

    return (
        <div className="grid grid-cols-2 h-screen">
            {/* Preparing Orders */}
            <div className="bg-yellow-100 p-4 overflow-y-auto">
                <h2 className="text-3xl font-bold text-center mb-4">Preparing ({preparingOrders.length})</h2>
                {preparingOrders.map(order => (
                    <div key={order.id} className="bg-white p-4 rounded-lg shadow mb-4">
                        <h3 className="font-bold">Order #{order.id}</h3>
                        <ul>
                            {order.items.map((item, index) => (
                                <li key={index}>{item.name} x {item.quantity}</li>
                            ))}
                        </ul>
                        <p className="font-semibold mt-2">Total: ${order.total_price.toFixed(2)}</p>
                        <button 
                            onClick={() => updateStatus(order.id, 'Ready')}
                            className="w-full bg-green-500 text-white mt-4 py-2 rounded"
                        >
                            Mark as Ready
                        </button>
                    </div>
                ))}
            </div>
            {/* Ready Orders */}
            <div className="bg-green-100 p-4 overflow-y-auto">
                <h2 className="text-3xl font-bold text-center mb-4">Ready ({readyOrders.length})</h2>
                {readyOrders.map(order => (
                     <div key={order.id} className="bg-white p-4 rounded-lg shadow mb-4 opacity-70">
                        <h3 className="font-bold">Order #{order.id}</h3>
                        <ul>
                            {order.items.map((item, index) => (
                                <li key={index}>{item.name} x {item.quantity}</li>
                            ))}
                        </ul>
                        <p className="font-semibold mt-2">Total: ${order.total_price.toFixed(2)}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

// Fetch initial orders on server-side
export async function getServerSideProps() {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/orders`);
    const initialOrders = await res.json();
    return { props: { initialOrders } };
}
