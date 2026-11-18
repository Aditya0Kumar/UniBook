from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.bookings.models import Booking
from .models import Payment


@login_required
def payment_checkout_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.payment_status not in (Booking.PAYMENT_PENDING, Booking.PAYMENT_FAILED) or booking.facility.booking_price <= 0:
        messages.info(request, "This booking has no pending payment.")
        return redirect('bookings:booking_detail', pk=booking.id)

    if booking.status not in (Booking.STATUS_CONFIRMED, Booking.STATUS_PENDING):
        messages.error(request, f"This booking is {booking.get_status_display().lower()} and can no longer be paid for.")
        return redirect('bookings:booking_detail', pk=booking.id)

    if request.method == 'POST':
        method = request.POST.get('payment_method', Payment.METHOD_CAMPUS_CARD)
        amount = booking.facility.booking_price

        # Process payment record
        payment = Payment.objects.create(
            booking=booking,
            user=request.user,
            amount=amount,
            currency='INR',
            status=Payment.STATUS_COMPLETED,
            payment_method=method,
            notes='Paid via UniBook secure portal'
        )

        booking.payment_status = Booking.PAYMENT_PAID
        booking.save()

        messages.success(request, f"Payment of ₹{amount} successful! Transaction ID: {payment.transaction_id}")
        return redirect('bookings:booking_detail', pk=booking.id)

    context = {
        'booking': booking,
        'amount': booking.facility.booking_price,
    }
    return render(request, 'student/checkout.html', context)
