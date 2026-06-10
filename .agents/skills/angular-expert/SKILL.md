---
name: angular-expert
description: Angular frontend expert. Use when working with Angular projects, components, services, or needing Angular best practices.
---

# Angular Expert

Expert in Angular 17+ with signals, standalone components, and modern patterns.

## When to Use This Skill

- Building Angular applications
- Creating components, services, or directives
- Angular migration or upgrades
- Debugging Angular issues
- Setting up Angular testing

## Angular 18+ Features

### Signals (Reactive Primitive)

```typescript
import { signal, computed, effect, signalStore } from '@angular/core';

// Basic signal
const count = signal(0);
const double = computed(() => count() * 2);

// Read/write
count.set(5);
count.update(v => v + 1);

// Effect (reactive side effect)
effect(() => {
  console.log(`Count changed: ${count()}`);
});
```

### Signal-based Services

```typescript
import { Injectable, computed, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class CartService {
  private items = signal<CartItem[]>([]);

  readonly totalItems = computed(() => this.items().length);
  readonly totalPrice = computed(() =>
    this.items().reduce((sum, item) => sum + item.price, 0)
  );

  addItem(item: CartItem) {
    this.items.update(items => [...items, item]);
  }

  removeItem(id: string) {
    this.items.update(items => items.filter(i => i.id !== id));
  }
}
```

### Standalone Components

```typescript
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-user-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card" [class.selected]="selected()">
      <img [src]="user.avatar" [alt]="user.name" />
      <h3>{{ user.name }}</h3>
      <p>{{ user.email }}</p>
      <button (click)="onSelect()">Select</button>
    </div>
  `,
  styles: [`
    .card { padding: 1rem; border: 1px solid #ddd; }
    .selected { border-color: blue; }
  `]
})
export class UserCardComponent {
  @Input({ required: true }) user!: User;
  @Input() selected = signal(false);
  @Output() select = new EventEmitter<User>();

  onSelect() {
    this.select.emit(this.user);
  }
}
```

### New Control Flow (@for, @if, @switch)

```typescript
@Component({
  template: `
    @if (isLoading()) {
      <app-loader />
    } @else {
      @for (item of items(); track item.id) {
        <div class="item">{{ item.name }}</div>
      } @empty {
        <p>No items found</p>
      }
    }

    @switch (status()) {
      @case ('loading') { <spinner /> }
      @case ('error') { <error-msg /> }
      @default { <content /> }
    }
  `
})
export class ListComponent {
  items = signal<Item[]>([]);
  isLoading = signal(true);
  status = signal<'loading' | 'error' | 'success'>('loading');
}
```

### Deferred Loading (@defer)

```typescript
@Component({
  template: `
    <h1>My App</h1>

    @defer (on viewport) {
      <heavy-chart-component />
    } @placeholder {
      <div>Loading chart...</div>
    } @loading {
      <spinner />
    } @error {
      <p>Failed to load</p>
    }

    @defer (on interaction) {
      <comments-section />
    } @placeholder {
      <button>Load comments</button>
    }
  `
})
export class DashboardComponent {}
```

## Project Structure

```
src/
├── app/
│   ├── core/                    # Singleton services, guards, interceptors
│   │   ├── services/
│   │   ├── guards/
│   │   └── interceptors/
│   ├── shared/                  # Shared components, pipes, directives
│   │   ├── components/
│   │   ├── pipes/
│   │   └── directives/
│   ├── features/                # Feature modules/routes
│   │   ├── dashboard/
│   │   │   ├── components/
│   │   │   └── services/
│   │   └── users/
│   ├── app.component.ts
│   ├── app.config.ts
│   └── app.routes.ts
├── assets/
├── environments/
└── styles.scss
```

## Routing (Functional Routes)

```typescript
// app.routes.ts
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./home/home.component').then(m => m.HomeComponent)
  },
  {
    path: 'users',
    loadChildren: () => import('./users/users.routes').then(m => m.USER_ROUTES)
  },
  {
    path: 'admin',
    loadComponent: () => import('./admin/admin.component').then(m => m.AdminComponent),
    canActivate: [authGuard]
  },
  {
    path: '**',
    redirectTo: ''
  }
];
```

## Dependency Injection

```typescript
import { inject } from '@angular/core';

// In component
export class ProfileComponent {
  private http = inject(HttpClient);
  private store = inject(StoreService);

  ngOnInit() {
    this.http.get('/api/user').subscribe(user => {
      this.store.setUser(user);
    });
  }
}

// Service with factory
@Injectable({ providedIn: 'root' })
export class ConfigService {
  private http = inject(HttpClient);

  loadConfig() {
    return this.http.get<Config>('/config');
  }
}
```

## Forms (Reactive)

```typescript
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()">
      <input formControlName="name" placeholder="Name" />
      @if (form.get('name')?.hasError('required') && form.get('name')?.touched) {
        <span class="error">Name is required</span>
      }

      <input formControlName="email" placeholder="Email" />
      <button type="submit" [disabled]="form.invalid">Submit</button>
    </form>
  `
})
export class UserFormComponent {
  private fb = inject(FormBuilder);

  form = this.fb.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]]
  });

  onSubmit() {
    if (this.form.valid) {
      console.log(this.form.value);
    }
  }
}
```

## HTTP Client

```typescript
import { HttpClient, HttpInterceptorFn } from '@angular/common/http';

const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem('token');
  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
  }
  return next(req);
};

// app.config.ts
export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(withInterceptors([authInterceptor]))
  ]
};
```

## Testing

```typescript
import { TestBed } from '@angular/core/testing';
import { ComponentFixture } from '@angular/core/testing';

describe('UserService', () => {
  let service: UserService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [UserService]
    });
    service = TestBed.inject(UserService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});

describe('UserCardComponent', () => {
  let component: UserCardComponent;
  let fixture: ComponentFixture<UserCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserCardComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(UserCardComponent);
    component = fixture.componentInstance;
    component.user = { id: '1', name: 'Test', email: 'test@test.com', avatar: '' };
    fixture.detectChanges();
  });

  it('should display user name', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h3')?.textContent).toContain('Test');
  });

  it('should emit select on button click', () => {
    jest.spyOn(component.select, 'emit');
    fixture.nativeElement.querySelector('button').click();
    expect(component.select.emit).toHaveBeenCalledWith(component.user);
  });
});
```

## State Management (SignalStore)

```typescript
import { patchState, signalStore, withMethods, withState } from '@ngrx/signals';

type UserState = {
  users: User[];
  loading: boolean;
  error: string | null;
};

const initialState: UserState = {
  users: [],
  loading: false,
  error: null
};

@Injectable()
export class UserStore extends signalStore(withState(initialState)) {
  private http = inject(HttpClient);

  loadUsers = withMethods(this, {
    loading: patchState({ loading: true, error: null }),
    success: patchState({ users: [], loading: false }),
    failure: (state, error: string) => patchState({ error, loading: false })
  });
}
```

## Angular CLI Commands

```bash
# New project (standalone by default)
ng new my-app --style=scss --routing

# Generate component
ng g c features/users/user-list --standalone

# Generate service
ng g s core/services/auth

# Generate guard
ng g guard core/guards/auth

# Build for production
ng build --configuration=production

# Run tests
ng test

# Run with coverage
ng test --coverage
```

## Best Practices

1. **Standalone Components**: Default in Angular 15+
2. **Signals**: Use for local state, signals everywhere
3. **Functional Interceptors/Guards**: Replace class-based
4. **OnPush**: Default change detection strategy
5. **Lazy Loading**: Route-level and component-level
6. **Strict Mode**: Enable in tsconfig

## Dependencies

Common packages:
- `@angular/core` ^18.0.0
- `@ngrx/signals` - State management
- `rxjs` - Reactive operators
- `@angular/forms` - Reactive/template forms
- `@angular/router` - Routing
- `zone.js` - Change detection
- `jasmine` / `jest` - Testing

## When Helping

- Check Angular version in package.json
- Use standalone components for new code
- Prefer signals over RxJS for local state
- Use new control flow syntax (@if, @for)
- Recommend @defer for heavy components