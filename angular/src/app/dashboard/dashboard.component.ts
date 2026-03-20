import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { MenuModule } from 'primeng/menu';
import { TagModule } from 'primeng/tag';
import { AuthService } from '../services/auth.service';
import { User, UserRole } from '../models/user.model';
import { ClusterAdminViewComponent } from './views/cluster-admin-view.component';
import { CompanyOwnerViewComponent } from './views/company-owner-view.component';
import { UtilityProviderViewComponent } from './views/utility-provider-view.component';

@Component({
    selector: 'app-dashboard',
    standalone: true,
    imports: [
        CommonModule,
        CardModule,
        ButtonModule,
        AvatarModule,
        MenuModule,
        TagModule,
        ClusterAdminViewComponent,
        CompanyOwnerViewComponent,
        UtilityProviderViewComponent
    ],
    templateUrl: './dashboard.component.html',
    styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
    user = signal<User | null>(null);
    loading = signal(true);
    UserRole = UserRole;


    constructor(
        private authService: AuthService,
        private router: Router

    ) { }

    ngOnInit() {
        this.authService.getMe().subscribe({
            next: (user) => {
                this.user.set(user);
                this.loading.set(false);
            },
            error: (error) => {
                console.error('Failed to load user:', error);
                this.loading.set(false);
                this.router.navigate(['/login']);
            }
        });
    }

    onLogout() {

        this.authService.logout();
        this.router.navigate(['/login']);
    }

    getUserInitials(): string {
        const user = this.user();
        if (!user) return '?';

        if (user.name) {
            const names = user.name.split(' ');
            if (names.length >= 2) {
                return names[0][0] + names[names.length - 1][0];
            }
            return names[0][0];
        }

        if (user.email) {
            return user.email[0].toUpperCase();
        }

        return '?';
    }

    getRoleBadgeLabel(): string {
        const user = this.user();
        if (!user) return '';
        switch (user.role) {
            case UserRole.CLUSTER_ADMIN:
                return 'Cluster Administrator';
            case UserRole.COMPANY_OWNER:
                return 'Company Owner';
            case UserRole.UTILITY_PROVIDER:
                return 'Utility Provider';
            default:
                return '';
        }
    }

    getRoleBadgeSeverity(): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
        const user = this.user();
        if (!user) return 'secondary';

        switch (user.role) {
            case UserRole.CLUSTER_ADMIN:
                return 'danger';
            case UserRole.COMPANY_OWNER:
                return 'info';
            case UserRole.UTILITY_PROVIDER:
                return 'success';
            default:
                return 'secondary';
        }
    }

    goToAddPlant() {
        this.router.navigate(['/add-plant']);
    }

    goToPlantsList() {
        this.router.navigate(['/plants']);
    }
}
