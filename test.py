# location / {
#     proxy_pass http://localhost:8000;
#     proxy_http_version 1.1;

#     # Add these missing headers
#     proxy_set_header X-Real-IP $remote_addr;
#     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#     proxy_set_header X-Forwarded-Proto $scheme;
#     proxy_set_header Host $host;

#     # Keep these
#     proxy_set_header Upgrade $http_upgrade;
#     proxy_set_header Connection 'upgrade';
#     proxy_cache_bypass $http_upgrade;

#     # Add timeout settings for webhooks
#     proxy_connect_timeout 60s;
#     proxy_send_timeout 60s;
#     proxy_read_timeout 60s;
# }



# class Customer(BaseModel):
#     phone = PhoneNumberField()
#     source = models.ForeignKey(
#         Category,
#         on_delete=models.PROTECT,
#         limit_choices_to={"category_type": "CUSTOMER_SOURCE"},
#         related_name="customer_source",
#     )
#     type = models.CharField(
#         max_length=20, choices=CustomerType.choices, default=CustomerType.LEAD
#     )

#     # Fk
#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE, related_name="user_customers"
#     )

#     class Meta:
#         unique_together = ["phone", "user"]

#     def __str__(self):
#         return f"Customer {self.uid} - {self.user.first_name} {self.user.last_name} - {self.salon.name}"


# class SalonCustomer(BaseModel):
#     customer = models.ForeignKey(
#         Customer, on_delete=models.CASCADE, related_name="salon_customers"
#     )
#     salon = models.ForeignKey(
#         Salon, on_delete=models.CASCADE, related_name="salon_customers"
#     )
#     account = models.ForeignKey(
#         Account, on_delete=models.CASCADE, related_name="account_salon_customers"
#     )

#     class Meta:
#         unique_together = ["customer", "salon"]

#     def __str__(self):
#         return f"SalonCustomer {self.uid} - {self.customer.phone} - {self.salon.name}"
