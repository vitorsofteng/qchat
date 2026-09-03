import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Router, RouterLink } from '@angular/router';
import { switchMap } from 'rxjs';

import { AuthService } from '../../core/services/auth.service';
import { WebSocketService } from '../../core/services/websocket.service';

/** Tela de cadastro com validacao reativa espelhando o backend (F14.1). */
@Component({
  selector: 'app-register',
  imports: [
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatProgressBarModule,
  ],
  templateUrl: './register.component.html',
  styleUrl: './auth.scss',
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly ws = inject(WebSocketService);
  private readonly router = inject(Router);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    username: [
      '',
      [
        Validators.required,
        Validators.minLength(3),
        Validators.maxLength(32),
        Validators.pattern(/^[a-zA-Z0-9]+$/),
      ],
    ],
    password: ['', [Validators.required, Validators.minLength(8), Validators.maxLength(72)]],
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    const { username, password } = this.form.getRawValue();

    this.auth
      .register(username, password)
      .pipe(switchMap(() => this.auth.login(username, password)))
      .subscribe({
        next: () => {
          const token = this.auth.token;
          if (token) {
            this.ws.connect(token);
          }
          void this.router.navigate(['/lobby']);
        },
        error: (response: HttpErrorResponse) => {
          this.loading.set(false);
          this.error.set(
            response.status === 409
              ? 'Este nome de usuário já está em uso.'
              : 'Não foi possível concluir o cadastro. Tente novamente.',
          );
        },
      });
  }
}
