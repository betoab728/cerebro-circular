import { writable } from 'svelte/store';
import { browser } from '$app/environment';

interface User {
    email: string;
    full_name: string;
    is_active: bool;
    id: number;
}

interface AuthState {
    isAuthenticated: boolean;
    token: string | null;
    user: User | null;
}

const initialState: AuthState = {
    isAuthenticated: false,
    token: null,
    user: null,
};

// Initialize from localStorage if available
function getInitialState(): AuthState {
    if (browser) {
        const token = localStorage.getItem('token');
        if (token) {
            return { isAuthenticated: true, token, user: null }; // We verify token valid later or load user profile
        }
    }
    return initialState;
}

export const auth = writable<AuthState>(getInitialState());

export const login = (token: string) => {
    if (browser) {
        localStorage.setItem('token', token);
    }
    auth.update(state => ({ ...state, isAuthenticated: true, token }));
};

export const logout = () => {
    if (browser) {
        localStorage.removeItem('token');
    }
    auth.set(initialState);
};
