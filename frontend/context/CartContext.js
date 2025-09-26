import React, { createContext, useState, useContext } from 'react';

const CartContext = createContext();

export const useCart = () => useContext(CartContext);

export const CartProvider = ({ children }) => {
    const [cartItems, setCartItems] = useState([]);

    const addToCart = (item) => {
        setCartItems(prevItems => {
            const existing = prevItems.find(i => i.id === item.id);
            if (existing) {
                return prevItems.map(i =>
                    i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i
                );
            }
            return [...prevItems, { ...item, quantity: 1 }];
        });
    };
    
    const clearCart = () => setCartItems([]);

    const total = cartItems.reduce((acc, item) => acc + item.price * item.quantity, 0);

    return (
        <CartContext.Provider value={{ cartItems, addToCart, clearCart, total }}>
            {children}
        </CartContext.Provider>
    );
};
