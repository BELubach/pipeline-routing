import { inject } from '@angular/core';
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { throwError, BehaviorSubject } from 'rxjs';
import { catchError, filter, take, switchMap } from 'rxjs/operators';
import { AuthService } from './auth.service';

let isRefreshing = false;
const refreshTokenSubject = new BehaviorSubject<string | null>(null);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  
  // Skip auth for specific endpoints
  if (req.url.includes('/pipelines/nodes')) {
    return next(req);
  }
  
  // Add access token to requests
  const accessToken = authService.getAccessToken();
  if (accessToken) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${accessToken}`
      }
    });
  }

  return next(req).pipe(
    catchError(error => {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        // Handle token refresh
        if (!isRefreshing) {
          isRefreshing = true;
          refreshTokenSubject.next(null);

          return authService.refresh().pipe(
            switchMap((response) => {
              isRefreshing = false;
              refreshTokenSubject.next(response.access_token);
              
              // Retry the failed request with new token
              const clonedReq = req.clone({
                setHeaders: {
                  Authorization: `Bearer ${response.access_token}`
                }
              });
              return next(clonedReq);
            }),
            catchError((err) => {
              isRefreshing = false;
              authService.logout();
              return throwError(() => err);
            })
          );
        } else {
          // Wait for refresh to complete
          return refreshTokenSubject.pipe(
            filter(token => token !== null),
            take(1),
            switchMap(token => {
              const clonedReq = req.clone({
                setHeaders: {
                  Authorization: `Bearer ${token}`
                }
              });
              return next(clonedReq);
            })
          );
        }
      }
      return throwError(() => error);
    })
  );
};
