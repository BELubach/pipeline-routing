import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { PasswordModule } from 'primeng/password';
import { CheckboxModule } from 'primeng/checkbox';
import { MessageModule } from 'primeng/message';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    InputTextModule,
    ButtonModule,
    PasswordModule,
    CheckboxModule,
    MessageModule
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  email = signal('');
  password = signal('');
  rememberMe = signal(false);
  errorMessage = signal('');
  loading = signal(false);

  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  onLogin() {
    this.loading.set(true);
    this.errorMessage.set('');

    if (!this.email() || !this.password()) {
      this.errorMessage.set('Please enter both email and password');
      this.loading.set(false);
      return;
    }

    this.authService.login({
      email: this.email(),
      password: this.password()
    }).subscribe({
      next: () => {
        this.authService.getMe().subscribe({
          next: () => {
            this.router.navigate(['/dashboard']);
          },
          error: (error) => {
            console.error('Failed to get user info:', error);
            this.router.navigate(['/dashboard']);
          }
        });
      },
      error: (error) => {
        console.error('Login failed:', error);
        if (error.status === 401) {
          this.errorMessage.set('Invalid email or password');
        } else if (error.status === 0) {
          this.errorMessage.set('Cannot connect to server. Please try again later.');
        } else {
          this.errorMessage.set(error.error?.message || 'Login failed. Please try again.');
        }
        this.loading.set(false);
      }
    });
  }
}
