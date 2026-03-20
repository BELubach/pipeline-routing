import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { User } from '../models/user.model';

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private accessToken = signal<string | null>(null);
  private refreshToken = signal<string | null>(null);
  private currentUser = signal<User | null>(null);

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    // Load tokens from localStorage on init
    const storedAccessToken = localStorage.getItem('access_token');
    const storedRefreshToken = localStorage.getItem('refresh_token');
    
    if (storedAccessToken) {
      this.accessToken.set(storedAccessToken);
    }
    if (storedRefreshToken) {
      this.refreshToken.set(storedRefreshToken);
    }
  }

  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>('/api/v1/auth/login', credentials)
      .pipe(
        tap(response => {
          this.setTokens(response.access_token, response.refresh_token);
        }),
        catchError(error => {
          console.error('Login error:', error);
          return throwError(() => error);
        })
      );
  }

  register(credentials: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>('/api/v1/auth/register', credentials)
      .pipe(
        tap(response => {
          this.setTokens(response.access_token, response.refresh_token);
        }),
        catchError(error => {
          console.error('Register error:', error);
          return throwError(() => error);
        })
      );
  }

  refresh(): Observable<AuthResponse> {
    const token = this.refreshToken();
    if (!token) {
      return throwError(() => new Error('No refresh token available'));
    }

    return this.http.post<AuthResponse>('/api/v1/auth/refresh', {
      refresh_token: token
    }).pipe(
      tap(response => {
        this.setTokens(response.access_token, response.refresh_token);
      }),
      catchError(error => {
        console.error('Refresh error:', error);
        this.logout();
        return throwError(() => error);
      })
    );
  }

  getMe(): Observable<User> {
    return this.http.get<User>('/api/v1/auth/me')
      .pipe(
        tap(user => {
          this.currentUser.set(user);
        }),
        catchError(error => {
          console.error('Get user error:', error);
          return throwError(() => error);
        })
      );
  }

  logout(): void {
    this.accessToken.set(null);
    this.refreshToken.set(null);
    this.currentUser.set(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.router.navigate(['/login']);
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    this.accessToken.set(accessToken);
    this.refreshToken.set(refreshToken);
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  getAccessToken(): string | null {
    return this.accessToken();
  }

  getRefreshToken(): string | null {
    return this.refreshToken();
  }

  isAuthenticated(): boolean {
    return !!this.accessToken();
  }

  getCurrentUser(): User | null {
    return this.currentUser();
  }
}
