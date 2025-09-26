import { useCart } from '../context/CartContext';
import { useRouter } from 'next/router';

export default function CartPage() {
    const { cartItems, total, clearCart } = useCart();
    const router = useRouter();

    const handlePlaceOrder = async () => {
        const orderData = {
            items: cartItems.map(item => ({ 
                id: item.id, 
                name: item.item_name, 
                quantity: item.quantity 
            })),
            total_price: total,
            payment_method: 'Cash on Pickup'
        };

        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
        });

        if (res.ok) {
            alert('Order placed successfully!');
            clearCart();
            router.push('/');
        } else {
            alert('Failed to place order.');
        }
    };

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-3xl font-bold mb-6">Your Cart</h1>
            {cartItems.length === 0 ? (
                <p>Your cart is empty.</p>
            ) : (
                <>
                    {cartItems.map(item => (
                        <div key={item.id} className="flex justify-between items-center border-b py-2">
                            <span>{item.item_name} x {item.quantity}</span>
                            <span>${(item.price * item.quantity).toFixed(2)}</span>
                        </div>
                    ))}
                    <div className="text-2xl font-bold text-right mt-4">
                        Total: ${total.toFixed(2)}
                    </div>
                    <button
                        onClick={handlePlaceOrder}
                        className="w-full bg-green-500 text-white mt-6 py-3 rounded text-lg"
                    >
                        Place Order (Cash on Pickup)
                    </button>
                </>
            )}
        </div>
    );
}
