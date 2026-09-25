import api from "./api";


// ==========================================================
// Types
// ==========================================================

export interface AuthUser {
  id: number;
  email: string;
}


export interface LoginResponse {
  access_token: string;
  token_type: string;
}


export interface RegisterResponse {
  id: number;
  email: string;
}


// ==========================================================
// Login
// ==========================================================

export async function loginUser(
  email: string,
  password: string
): Promise<LoginResponse> {

  const formData =
    new URLSearchParams();


  formData.append(
    "username",
    email
  );


  formData.append(
    "password",
    password
  );


  const response =
    await api.post<LoginResponse>(
      "/auth/token",
      formData,
      {
        headers: {
          "Content-Type":
            "application/x-www-form-urlencoded",
        },
      }
    );


  return response.data;
}


// ==========================================================
// Register
// ==========================================================

export async function registerUser(
  email: string,
  password: string
): Promise<RegisterResponse> {

  const response =
    await api.post<RegisterResponse>(
      "/auth/register",
      {
        email,
        password,
      }
    );


  return response.data;
}


// ==========================================================
// Get Current Logged-In User
// ==========================================================

export async function getCurrentUser():
  Promise<AuthUser> {

  const response =
    await api.get<AuthUser>(
      "/auth/me"
    );


  return response.data;
}


// ==========================================================
// Logout
// ==========================================================

export function logoutUser() {

  sessionStorage.removeItem(
    "access_token"
  );

}


// ==========================================================
// Check Authentication
// ==========================================================

export function isAuthenticated():
  boolean {

  return Boolean(
    sessionStorage.getItem(
      "access_token"
    )
  );

}