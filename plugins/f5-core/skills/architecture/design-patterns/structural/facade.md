---
name: facade-pattern
description: Facade pattern for simplified interfaces
category: architecture/design-patterns/structural
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Facade Pattern

## Overview

The Facade pattern provides a unified interface to a set of interfaces
in a subsystem. It defines a higher-level interface that makes the
subsystem easier to use.

## Problem

```typescript
// ❌ Client must know and coordinate multiple subsystems
class OrderProcessor {
  async processOrder(orderData: OrderData): Promise<void> {
    // Client must know all subsystems
    const inventory = new InventoryService();
    const payment = new PaymentGateway();
    const shipping = new ShippingService();
    const notification = new NotificationService();
    const analytics = new AnalyticsService();
    const fraud = new FraudDetectionService();

    // Client must coordinate them correctly
    await fraud.check(orderData);
    await inventory.reserve(orderData.items);
    await payment.charge(orderData.paymentDetails);
    const shipment = await shipping.createShipment(orderData);
    await notification.sendConfirmation(orderData.email, shipment);
    await analytics.trackOrder(orderData);

    // What if payment fails after inventory reserved?
    // Client must handle all error cases and rollback
  }
}
```

## Solution: Facade

```typescript
// ✅ Facade hides complexity behind simple interface
class OrderFacade {
  constructor(
    private readonly inventory: InventoryService,
    private readonly payment: PaymentGateway,
    private readonly shipping: ShippingService,
    private readonly notification: NotificationService,
    private readonly analytics: AnalyticsService,
    private readonly fraud: FraudDetectionService
  ) {}

  async placeOrder(orderData: OrderData): Promise<OrderResult> {
    try {
      // Facade coordinates all subsystems
      await this.validateOrder(orderData);
      await this.processPayment(orderData);
      const shipment = await this.arrangeShipping(orderData);
      await this.notifyCustomer(orderData, shipment);
      await this.trackAnalytics(orderData);

      return { success: true, orderId: orderData.id, shipment };
    } catch (error) {
      await this.handleFailure(orderData, error);
      throw error;
    }
  }

  private async validateOrder(orderData: OrderData): Promise<void> {
    // Fraud check
    const fraudResult = await this.fraud.check(orderData);
    if (fraudResult.suspicious) {
      throw new FraudDetectedError(fraudResult.reason);
    }

    // Inventory check
    for (const item of orderData.items) {
      const available = await this.inventory.checkStock(item.productId, item.quantity);
      if (!available) {
        throw new OutOfStockError(item.productId);
      }
    }
  }

  private async processPayment(orderData: OrderData): Promise<void> {
    // Reserve inventory first
    const reservationId = await this.inventory.reserve(orderData.items);

    try {
      await this.payment.charge({
        amount: orderData.total,
        currency: orderData.currency,
        method: orderData.paymentDetails,
      });
    } catch (error) {
      // Rollback on payment failure
      await this.inventory.release(reservationId);
      throw error;
    }
  }

  private async arrangeShipping(orderData: OrderData): Promise<Shipment> {
    return this.shipping.createShipment({
      items: orderData.items,
      address: orderData.shippingAddress,
      method: orderData.shippingMethod,
    });
  }

  private async notifyCustomer(orderData: OrderData, shipment: Shipment): Promise<void> {
    await this.notification.sendOrderConfirmation({
      email: orderData.email,
      orderId: orderData.id,
      trackingNumber: shipment.trackingNumber,
    });
  }

  private async trackAnalytics(orderData: OrderData): Promise<void> {
    await this.analytics.track('order_placed', {
      orderId: orderData.id,
      total: orderData.total,
      itemCount: orderData.items.length,
    });
  }

  private async handleFailure(orderData: OrderData, error: Error): Promise<void> {
    await this.analytics.track('order_failed', {
      orderId: orderData.id,
      error: error.message,
    });
  }
}

// Client code is now simple
const orderFacade = new OrderFacade(/* ... dependencies ... */);
const result = await orderFacade.placeOrder(orderData);
```

## Real-World Examples

### Email Service Facade

```typescript
// Complex subsystems
class SmtpClient { /* ... */ }
class TemplateEngine { /* ... */ }
class AttachmentProcessor { /* ... */ }
class EmailValidator { /* ... */ }
class EmailQueue { /* ... */ }
class BounceHandler { /* ... */ }

// Facade simplifies email operations
class EmailFacade {
  constructor(
    private smtp: SmtpClient,
    private templates: TemplateEngine,
    private attachments: AttachmentProcessor,
    private validator: EmailValidator,
    private queue: EmailQueue,
    private bounceHandler: BounceHandler
  ) {}

  async sendTemplatedEmail(options: TemplatedEmailOptions): Promise<EmailResult> {
    // Validate
    const validationResult = this.validator.validate(options.to);
    if (!validationResult.valid) {
      throw new InvalidEmailError(options.to);
    }

    // Check bounce status
    if (await this.bounceHandler.isBounced(options.to)) {
      throw new BouncedEmailError(options.to);
    }

    // Render template
    const html = await this.templates.render(options.template, options.data);

    // Process attachments
    const processedAttachments = options.attachments
      ? await this.attachments.process(options.attachments)
      : [];

    // Queue for sending
    const emailId = await this.queue.add({
      to: options.to,
      from: options.from || this.getDefaultFrom(),
      subject: options.subject,
      html,
      attachments: processedAttachments,
      priority: options.priority || 'normal',
    });

    return { emailId, status: 'queued' };
  }

  async sendSimpleEmail(to: string, subject: string, body: string): Promise<EmailResult> {
    return this.sendTemplatedEmail({
      to,
      subject,
      template: 'simple',
      data: { body },
    });
  }

  async sendWelcomeEmail(user: User): Promise<EmailResult> {
    return this.sendTemplatedEmail({
      to: user.email,
      subject: 'Welcome!',
      template: 'welcome',
      data: { name: user.name, loginUrl: this.getLoginUrl() },
      priority: 'high',
    });
  }

  async sendPasswordResetEmail(user: User, token: string): Promise<EmailResult> {
    return this.sendTemplatedEmail({
      to: user.email,
      subject: 'Reset Your Password',
      template: 'password-reset',
      data: { name: user.name, resetUrl: this.getResetUrl(token) },
      priority: 'high',
    });
  }

  private getDefaultFrom(): string {
    return 'noreply@company.com';
  }

  private getLoginUrl(): string {
    return `${process.env.APP_URL}/login`;
  }

  private getResetUrl(token: string): string {
    return `${process.env.APP_URL}/reset-password?token=${token}`;
  }
}

// Usage - simple and clear
const emailFacade = new EmailFacade(/* ... */);
await emailFacade.sendWelcomeEmail(newUser);
await emailFacade.sendPasswordResetEmail(user, resetToken);
```

### File Storage Facade

```typescript
// Complex cloud storage subsystems
class S3Client { /* ... */ }
class CloudFrontManager { /* ... */ }
class ImageProcessor { /* ... */ }
class VideoTranscoder { /* ... */ }
class MetadataExtractor { /* ... */ }
class AccessControlManager { /* ... */ }

// Facade for file operations
class StorageFacade {
  constructor(
    private s3: S3Client,
    private cdn: CloudFrontManager,
    private imageProcessor: ImageProcessor,
    private videoTranscoder: VideoTranscoder,
    private metadata: MetadataExtractor,
    private acl: AccessControlManager
  ) {}

  async uploadFile(file: Buffer, options: UploadOptions): Promise<UploadResult> {
    // Extract metadata
    const meta = await this.metadata.extract(file, options.mimeType);

    // Generate unique key
    const key = this.generateKey(options.filename, meta);

    // Process based on type
    let processedFile = file;
    if (this.isImage(options.mimeType)) {
      processedFile = await this.imageProcessor.optimize(file, options.imageOptions);
    }

    // Upload to S3
    await this.s3.upload({
      key,
      body: processedFile,
      contentType: options.mimeType,
      metadata: meta,
    });

    // Set access control
    await this.acl.setPermissions(key, options.visibility || 'private');

    // Generate CDN URL if public
    const url = options.visibility === 'public'
      ? await this.cdn.getUrl(key)
      : await this.s3.getSignedUrl(key, options.urlExpiry || 3600);

    return { key, url, metadata: meta };
  }

  async uploadImage(file: Buffer, options: ImageUploadOptions): Promise<ImageUploadResult> {
    // Generate thumbnails
    const thumbnails = await this.imageProcessor.generateThumbnails(file, [
      { width: 100, height: 100, suffix: 'thumb' },
      { width: 400, height: 400, suffix: 'medium' },
      { width: 800, height: 800, suffix: 'large' },
    ]);

    // Upload all versions
    const results = await Promise.all([
      this.uploadFile(file, { ...options, filename: options.filename }),
      ...thumbnails.map((thumb, i) =>
        this.uploadFile(thumb.buffer, {
          ...options,
          filename: `${options.filename}-${thumb.suffix}`,
        })
      ),
    ]);

    return {
      original: results[0],
      thumbnails: {
        thumb: results[1],
        medium: results[2],
        large: results[3],
      },
    };
  }

  async uploadVideo(file: Buffer, options: VideoUploadOptions): Promise<VideoUploadResult> {
    // Upload original
    const original = await this.uploadFile(file, options);

    // Start transcoding job (async)
    const transcodingJob = await this.videoTranscoder.startJob({
      sourceKey: original.key,
      formats: options.formats || ['720p', '480p', '360p'],
      thumbnail: true,
    });

    return {
      original,
      transcodingJobId: transcodingJob.id,
      status: 'processing',
    };
  }

  async deleteFile(key: string): Promise<void> {
    // Delete from S3
    await this.s3.delete(key);
    // Invalidate CDN cache
    await this.cdn.invalidate(key);
  }

  private generateKey(filename: string, meta: Metadata): string {
    const hash = crypto.createHash('md5').update(filename + Date.now()).digest('hex');
    return `uploads/${meta.type}/${hash}/${filename}`;
  }

  private isImage(mimeType: string): boolean {
    return mimeType.startsWith('image/');
  }
}
```

### Authentication Facade

```typescript
class AuthFacade {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly passwordHasher: PasswordHasher,
    private readonly tokenService: TokenService,
    private readonly sessionManager: SessionManager,
    private readonly mfaService: MFAService,
    private readonly auditLogger: AuditLogger,
    private readonly rateLimiter: RateLimiter
  ) {}

  async login(credentials: LoginCredentials): Promise<LoginResult> {
    // Rate limiting
    await this.rateLimiter.checkLimit(credentials.email);

    // Find user
    const user = await this.userRepository.findByEmail(credentials.email);
    if (!user) {
      await this.auditLogger.log('login_failed', { email: credentials.email, reason: 'user_not_found' });
      throw new AuthenticationError('Invalid credentials');
    }

    // Verify password
    const passwordValid = await this.passwordHasher.verify(credentials.password, user.password);
    if (!passwordValid) {
      await this.auditLogger.log('login_failed', { userId: user.id, reason: 'invalid_password' });
      throw new AuthenticationError('Invalid credentials');
    }

    // Check MFA
    if (user.mfaEnabled) {
      if (!credentials.mfaCode) {
        return { requiresMfa: true, tempToken: await this.tokenService.createTempToken(user.id) };
      }
      const mfaValid = await this.mfaService.verify(user.id, credentials.mfaCode);
      if (!mfaValid) {
        throw new AuthenticationError('Invalid MFA code');
      }
    }

    // Create session and tokens
    const session = await this.sessionManager.create(user.id, credentials.deviceInfo);
    const tokens = await this.tokenService.createTokenPair(user.id, session.id);

    await this.auditLogger.log('login_success', { userId: user.id, sessionId: session.id });

    return {
      user: this.sanitizeUser(user),
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
    };
  }

  async logout(accessToken: string): Promise<void> {
    const payload = await this.tokenService.verify(accessToken);
    await this.sessionManager.invalidate(payload.sessionId);
    await this.tokenService.blacklist(accessToken);
    await this.auditLogger.log('logout', { userId: payload.userId });
  }

  async refreshTokens(refreshToken: string): Promise<TokenPair> {
    return this.tokenService.refresh(refreshToken);
  }

  private sanitizeUser(user: User): SafeUser {
    const { password, mfaSecret, ...safeUser } = user;
    return safeUser;
  }
}
```

## Facade vs Adapter

| Aspect | Facade | Adapter |
|--------|--------|---------|
| Purpose | Simplify complex subsystem | Make incompatible interfaces work |
| Scope | Entire subsystem | Single class/interface |
| Direction | New simple interface | Convert existing interface |
| Complexity | Reduces complexity | Maintains complexity |

## Benefits

| Benefit | Description |
|---------|-------------|
| Simplicity | Hides subsystem complexity |
| Decoupling | Clients don't depend on subsystems |
| Flexibility | Can change subsystems without affecting clients |
| Testability | Easy to mock facade for testing |
