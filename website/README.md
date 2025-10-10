# Workstation - AI Chat Hub

A modern React TypeScript application for seamless communication with friends, co-workers, and AI agents, all integrated with Google Calendar.

## 🚀 Features

- **Home Page**: Beautiful landing page showcasing product information
- **Google Authentication**: Secure login with Google OAuth
- **Google Calendar Integration**: Read/write access to user's calendar
- **User Dashboard**: Personalized dashboard with settings and agent customization
- **Responsive Design**: Mobile-first, works on all devices

## 📁 Project Structure

```
website/
├── public/
│   ├── index.html          # HTML template
│   └── ...                 # Static assets
├── src/
│   ├── assets/
│   │   └── images/         # Logo, hero, and other images
│   ├── components/
│   │   ├── HomePage/
│   │   │   ├── HomePage.tsx
│   │   │   └── HomePage.css
│   │   ├── LoginPage/
│   │   │   ├── LoginPage.tsx
│   │   │   └── LoginPage.css
│   │   └── Dashboard/
│   │       ├── Dashboard.tsx
│   │       ├── Dashboard.css
│   │       └── SidePanel/
│   │           ├── SidePanel.tsx
│   │           └── SidePanel.css
│   ├── App.tsx             # Main app component with routing
│   ├── App.css             # Global app styles
│   ├── index.tsx           # Application entry point
│   └── index.css           # Global styles and font imports
├── package.json
├── tsconfig.json
└── README.md
```

## 🎨 Code Standards

### Architecture Principles

1. **Modular Design**: Each component has its own directory with `.tsx` and `.css` files
2. **Component Structure**: All components use React Class components with named methods
3. **TypeScript**: Strict typing for props and state interfaces
4. **Separation of Concerns**: Clear separation between logic, styles, and markup

### Component Standards

#### Class-Based Components

All components must follow the class-based structure:

```typescript
import React, { Component } from 'react';
import './ComponentName.css';

interface ComponentNameProps {
  // Props interface
}

interface ComponentNameState {
  // State interface
}

class ComponentName extends Component<ComponentNameProps, ComponentNameState> {
  constructor(props: ComponentNameProps) {
    super(props);
    this.state = {
      // Initial state
    };
  }

  // Named methods (NO arrow functions)
  handleAction(): void {
    // Method logic
  }

  render() {
    return (
      <div className="component-name">
        {/* Component JSX */}
      </div>
    );
  }
}

export default ComponentName;
```

#### Key Rules

1. **NO Arrow Functions**: Always use named methods instead of arrow functions
   ```typescript
   // ❌ DON'T
   handleClick = () => { }
   
   // ✅ DO
   handleClick(): void { }
   ```

2. **Type Everything**: Define interfaces for props and state
   ```typescript
   interface Props {
     title: string;
     count: number;
   }
   
   interface State {
     isOpen: boolean;
   }
   ```

3. **Constructor Pattern**: Always initialize state in constructor
   ```typescript
   constructor(props: Props) {
     super(props);
     this.state = {
       isOpen: false
     };
   }
   ```

4. **Event Handlers**: Bind methods inline or use named methods with explicit return types
   ```typescript
   <button onClick={() => this.handleClick()}>Click</button>
   ```

### File Organization

1. **Component Directory**: Each component gets its own directory
   ```
   ComponentName/
   ├── ComponentName.tsx
   └── ComponentName.css
   ```

2. **Assets**: Images and static files go in `src/assets/`
   ```
   assets/
   └── images/
       ├── logo.png
       └── hero.png
   ```

3. **Nested Components**: Sub-components go in subdirectories
   ```
   Dashboard/
   ├── Dashboard.tsx
   ├── Dashboard.css
   └── SidePanel/
       ├── SidePanel.tsx
       └── SidePanel.css
   ```

### Styling Standards

1. **CSS Modules Pattern**: Each component has its own CSS file
2. **BEM-like Naming**: Use descriptive, component-scoped class names
   ```css
   .component-name { }
   .component-name-header { }
   .component-name-item { }
   ```

3. **Google Fonts**: Using "Be Vietnam Pro" font family
   ```css
   font-family: 'Be Vietnam Pro', sans-serif;
   ```

4. **Responsive Design**: Mobile-first approach with media queries
   ```css
   @media (max-width: 768px) {
     /* Mobile styles */
   }
   ```

### Naming Conventions

1. **Components**: PascalCase (e.g., `HomePage`, `SidePanel`)
2. **Files**: Match component name (e.g., `HomePage.tsx`, `HomePage.css`)
3. **Methods**: camelCase with descriptive names (e.g., `handleSectionChange`, `renderSettings`)
4. **CSS Classes**: kebab-case (e.g., `home-page`, `side-panel-item`)
5. **Constants**: UPPER_SNAKE_CASE for true constants

### TypeScript Best Practices

1. **Explicit Types**: Always define return types for methods
   ```typescript
   handleClick(): void { }
   getData(): string[] { }
   ```

2. **Interface First**: Define interfaces before using them
   ```typescript
   interface User {
     id: string;
     name: string;
   }
   ```

3. **No `any`**: Avoid using `any` type, use proper types or `unknown`

4. **Null Safety**: Handle null/undefined cases explicitly
   ```typescript
   const user: User | null = null;
   if (user) {
     // Safe to use user
   }
   ```

## 🛠️ Setup and Installation

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

```bash
# Navigate to the website directory
cd website

# Install dependencies
npm install

# Start development server
npm start
```

The application will open at `http://localhost:3000`

### Available Scripts

- `npm start` - Starts the development server
- `npm build` - Creates a production build
- `npm test` - Runs the test suite
- `npm eject` - Ejects from Create React App (one-way operation)

## 🔐 Authentication Setup

To enable Google OAuth and Calendar integration:

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Add authorized redirect URIs
5. Update the `LoginPage` component with your Client ID
6. Request the following scopes:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `https://www.googleapis.com/auth/userinfo.email`

## 🌐 Deployment

This application is designed to be deployed to a custom domain. Build the production version:

```bash
npm run build
```

The `build` folder will contain the optimized production build ready for deployment.

### Deployment Options

- **Vercel**: `vercel deploy`
- **Netlify**: Drag and drop the `build` folder
- **AWS S3 + CloudFront**: Upload to S3 and configure CloudFront
- **Custom Server**: Serve the `build` folder with any static file server

## 📝 Development Guidelines

### Adding a New Component

1. Create a new directory under `src/components/`
2. Create `ComponentName.tsx` and `ComponentName.css`
3. Follow the class-based component structure
4. Define Props and State interfaces
5. Use named methods, not arrow functions
6. Import and use in parent component

### Adding a New Page

1. Create the page component following standards
2. Add route in `App.tsx`:
   ```typescript
   <Route path="/new-page" element={<NewPage />} />
   ```
3. Update navigation as needed

### Styling Guidelines

- Keep styles scoped to components
- Use consistent spacing (rem units)
- Follow the existing color palette
- Maintain responsive design principles
- Test on multiple screen sizes

## 🎯 Routing Structure

- `/` - Home page (public)
- `/login` - Login page (public)
- `/dashboard` - User dashboard (authenticated only)

## 🔧 Technologies Used

- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **React Router v6** - Client-side routing
- **CSS3** - Styling
- **Google Fonts** - Be Vietnam Pro typography
- **Create React App** - Build tooling

## 📦 Dependencies

```json
{
  "react": "^18.x.x",
  "react-dom": "^18.x.x",
  "react-router-dom": "^6.x.x",
  "typescript": "^4.x.x"
}
```

## 🐛 Common Issues

### Issue: Component not rendering
- Check import paths
- Verify component is exported correctly
- Ensure route is configured in App.tsx

### Issue: Styles not applying
- Verify CSS file is imported in component
- Check class name spelling
- Clear browser cache

### Issue: TypeScript errors
- Run `npm install @types/[package-name]` for missing types
- Check interface definitions match usage
- Ensure return types are specified

## 🤝 Contributing

1. Follow the established code standards
2. Use class components with named methods
3. Write TypeScript with explicit types
4. Keep components modular and reusable
5. Test on multiple browsers and devices
6. Update documentation as needed

## 📄 License

This project is private and proprietary.

## 👥 Team

For questions or support, contact the development team.

---

**Note**: This is a TypeScript React application following class-based component architecture. All code should adhere to the standards outlined in this README.
