import { useCart } from '../context/CartContext';
import Link from 'next/link';

export default function MenuPage({ menuItems }) {
  const { addToCart, cartItems, total } = useCart();

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-4xl font-bold text-center my-8">Our Menu</h1>
      <div className="grid md:grid-cols-3 gap-6">
        {menuItems.map((item) => (
          <div key={item.id} className="border rounded-lg p-4 shadow-lg">
            <h2 className="text-2xl font-bold">{item.item_name}</h2>
            <p className="text-gray-600 my-2">{item.description}</p>
            <div className="flex justify-between items-center mt-4">
              <span className="text-xl font-semibold">${item.price.toFixed(2)}</span>
              <button
                onClick={() => addToCart(item)}
                className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition"
              >
                Add to Cart
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Cart Summary Floating Button */}
      {cartItems.length > 0 && (
        <div className="fixed bottom-10 right-10">
            <Link href="/cart">
                <a className="bg-blue-600 text-white px-6 py-4 rounded-full shadow-lg text-lg">
                    View Cart ({cartItems.reduce((acc, item) => acc + item.quantity, 0)}) - ${total.toFixed(2)}
                </a>
            </Link>
        </div>
      )}
    </div>
  );
}

// Fetch data at build time from your backend API
export async function getStaticProps() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/menu`);
  const menuItems = await res.json();
  return {
    props: { menuItems },
    revalidate: 60, // Re-fetch menu data every 60 seconds
  };
}
