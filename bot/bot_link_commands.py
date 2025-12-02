    async def link_account_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate a code to link Telegram account to web profile"""
        if await self.check_interview_lock(update, context): return
        
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        # Get or create platform user
        platform_user, created = await sync_to_async(User.objects.get_or_create)(
            telegram_id=user_id,
            defaults={
                'user_id': user_id,
                'username': username,
                'platform_type': 'telegram'
            }
        )
        
        # If user_id doesn't match telegram_id, update it
        if platform_user.user_id != user_id and not platform_user.telegram_id:
            platform_user.telegram_id = user_id
            await sync_to_async(platform_user.save)()
        
        # Check if already linked
        if platform_user.tenant_user:
            await update.message.reply_text(
                f"✅ *Account Already Linked*\\n\\n"
                f"Your Telegram account is linked to:\\n"
                f"📧 {platform_user.tenant_user.email}\\n"
                f"🏢 {platform_user.tenant_user.tenant.name}\\n\\n"
                f"Use /unlink to disconnect.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Generate link code
        code = await sync_to_async(platform_user.generate_link_code)()
        
        await update.message.reply_text(
            f"🔗 *Link Your Account*\\n\\n"
            f"Your linking code: `{code}`\\n\\n"
            f"⏰ This code expires in 15 minutes.\\n\\n"
            f"*To link your account:*\\n"
            f"1. Go to https://api.pluggedspace.org/job/settings/link\\n"
            f"2. Enter this code\\n"
            f"3. Your Telegram and web accounts will be linked!\\n\\n"
            f"*Benefits:*\\n"
            f"✅ Unified job alerts across platforms\\n"
            f"✅ Shared subscription status\\n"
            f"✅ Access your data from web or Telegram\\n"
            f"✅ Sync your CV and saved jobs",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def unlink_account_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unlink Telegram account from web profile"""
        if await self.check_interview_lock(update, context): return
        
        user_id = str(update.effective_user.id)
        
        try:
            platform_user = await sync_to_async(User.objects.get)(telegram_id=user_id)
        except User.DoesNotExist:
            await update.message.reply_text(
                "❌ No Telegram account found. Use /start to register first."
            )
            return
        
        if not platform_user.tenant_user:
            await update.message.reply_text(
                "ℹ️ Your Telegram account is not linked to any web profile.\\n\\n"
                "Use /link to link your account.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Store email for confirmation message
        email = platform_user.tenant_user.email
        
        # Unlink
        platform_user.tenant_user = None
        await sync_to_async(platform_user.save)()
        
        await update.message.reply_text(
            f"✅ *Account Unlinked*\\n\\n"
            f"Your Telegram account has been disconnected from:\\n"
            f"📧 {email}\\n\\n"
            f"You can link to a different account anytime using /link",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def account_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show account information and linking status"""
        if await self.check_interview_lock(update, context): return
        
        user_id = str(update.effective_user.id)
        
        try:
            platform_user = await sync_to_async(User.objects.get)(telegram_id=user_id)
        except User.DoesNotExist:
            await update.message.reply_text(
                "❌ No account found. Use /start to register first."
            )
            return
        
        # Build account info message
        message = f"👤 *Your Account Info*\\n\\n"
        message += f"*Telegram:*\\n"
        message += f"• Username: @{platform_user.username or 'Not set'}\\n"
        message += f"• User ID: `{platform_user.telegram_id}`\\n"
        message += f"• Subscription: {platform_user.subscription_status}\\n"
        message += f"• Searches: {platform_user.search_count}/{FREE_SEARCH_LIMIT}\\n\\n"
        
        if platform_user.tenant_user:
            message += f"*🔗 Linked Web Account:*\\n"
            message += f"• Email: {platform_user.tenant_user.email}\\n"
            message += f"• Name: {platform_user.tenant_user.full_name or 'Not set'}\\n"
            message += f"• Organization: {platform_user.tenant_user.tenant.name}\\n"
            message += f"• Role: {platform_user.tenant_user.role.title()}\\n\\n"
            message += f"Use /unlink to disconnect"
        else:
            message += f"*🔗 Account Linking:*\\n"
            message += f"Not linked to any web account\\n\\n"
            message += f"Use /link to link your account"
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

    def run(self):
        self.application.run_polling()
