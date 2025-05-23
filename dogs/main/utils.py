from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from django.http import HttpResponse
import os
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def generate_booking_pdf(booking):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="booking_{booking.id}.pdf"'
    
    p = canvas.Canvas(response, pagesize=A4)
    p.setFont("Times-Roman", 14)

    p.drawString(50, 800, f"Booking #{booking.id}")
    p.setFont("Times-Roman", 12)
    
    y = 750
    p.drawString(50, y, f"Status: {booking.get_status_display()}")
    y -= 20
    p.drawString(50, y, f"Start date: {booking.start_date}")
    y -= 20
    p.drawString(50, y, f"End date: {booking.end_date}")
    y -= 20
    p.drawString(50, y, f"Total price: {booking.total_price} RUB")
    
    # Информация о клиенте
    y -= 40
    p.drawString(50, y, "Client information:")
    y -= 20
    p.drawString(70, y, f"Name: {booking.user.get_full_name()}")
    y -= 20
    p.drawString(70, y, f"Email: {booking.user.email}")
    y -= 20
    p.drawString(70, y, f"Phone: {booking.user.phone or 'Not specified'}")
    
    # Информация о догситтере
    y -= 40
    p.drawString(50, y, "Dog sitter information:")
    y -= 20
    p.drawString(70, y, f"Name: {booking.dog_sitter.user.get_full_name()}")
    y -= 20
    p.drawString(70, y, f"Rating: {booking.dog_sitter.rating}")
    
    # Список животных
    y -= 40
    p.drawString(50, y, "Animals:")
    y -= 20
    
    # Создаем таблицу с животными
    data = [['Name', 'Type', 'Breed', 'Size', 'Special needs']]
    for animal in booking.animals.all():
        data.append([
            animal.name,
            animal.get_type_display(),
            animal.breed or 'Not specified',
            animal.get_size_display(),
            animal.special_needs or 'None'
        ])
    
    table = Table(data, colWidths=[80, 80, 100, 80, 150])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    table.wrapOn(p, 400, 200)
    table.drawOn(p, 50, y - 100)
    
    # Список услуг
    y -= 150
    p.drawString(50, y, "Services:")
    y -= 20
    
    for service in booking.services.all():
        p.drawString(70, y, f"• {service.name} - {service.price} RUB")
        y -= 20
    
    # Дополнительная информация
    y -= 40
    p.drawString(50, y, "Additional information:")
    y -= 20
    p.drawString(70, y, f"Created: {booking.created_at.strftime('%d.%m.%Y %H:%M')}")
    y -= 20
    p.drawString(70, y, f"Updated: {booking.updated_at.strftime('%d.%m.%Y %H:%M')}")
    
    # Подпись
    p.setFont("Times-Roman", 8)
    p.drawString(50, 50, "Document generated automatically")
    p.drawString(50, 35, f"Generation date: {timezone.now().strftime('%d.%m.%Y %H:%M')}")
    
    p.showPage()
    p.save()
    
    return response

def generate_dogsitter_report_pdf(dogsitter, start_date=None, end_date=None):
    """Генерирует PDF отчет о работе догситтера"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dogsitter_report_{dogsitter.id}.pdf"'
    
    p = canvas.Canvas(response, pagesize=A4)
    p.setFont("Times-Roman", 14)
    
    # Заголовок
    full_name = dogsitter.user.get_full_name() if dogsitter.user else "Unknown"
    p.drawString(50, 800, f"Dog Sitter Report: {full_name}")
    p.setFont("Times-Roman", 12)
    
    # Основная информация
    y = 750
    rating = dogsitter.rating if dogsitter.rating is not None else "Not rated"
    p.drawString(50, y, f"Rating: {rating}")
    y -= 20
    experience = dogsitter.experience_years if dogsitter.experience_years is not None else 0
    p.drawString(50, y, f"Experience: {experience} years")
    
    # Статистика
    stats = dogsitter.get_statistics() or {
        'bookings_stats': {
            'total_bookings': 0,
            'completed_bookings': 0,
            'cancelled_bookings': 0,
            'total_earnings': 0,
            'avg_booking_price': 0
        },
        'reviews_stats': {
            'total_reviews': 0,
            'avg_rating': 0,
            'five_star_reviews': 0,
            'four_star_reviews': 0,
            'three_star_reviews': 0
        }
    }
    
    y -= 40
    p.drawString(50, y, "Booking statistics:")
    y -= 20
    
    bookings_stats = stats.get('bookings_stats', {})
    p.drawString(70, y, f"Total bookings: {bookings_stats.get('total_bookings', 0)}")
    y -= 20
    p.drawString(70, y, f"Completed: {bookings_stats.get('completed_bookings', 0)}")
    y -= 20
    p.drawString(70, y, f"Cancelled: {bookings_stats.get('cancelled_bookings', 0)}")
    y -= 20
    p.drawString(70, y, f"Total earnings: {bookings_stats.get('total_earnings', 0)} RUB")
    y -= 20
    p.drawString(70, y, f"Average booking price: {bookings_stats.get('avg_booking_price', 0)} RUB")
    
    # Статистика по отзывам
    y -= 40
    p.drawString(50, y, "Review statistics:")
    y -= 20
    
    reviews_stats = stats.get('reviews_stats', {})
    p.drawString(70, y, f"Total reviews: {reviews_stats.get('total_reviews', 0)}")
    y -= 20
    avg_rating = reviews_stats.get('avg_rating', 0)
    p.drawString(70, y, f"Average rating: {avg_rating:.1f}")
    y -= 20
    p.drawString(70, y, f"5 stars: {reviews_stats.get('five_star_reviews', 0)}")
    y -= 20
    p.drawString(70, y, f"4 stars: {reviews_stats.get('four_star_reviews', 0)}")
    y -= 20
    p.drawString(70, y, f"3 stars: {reviews_stats.get('three_star_reviews', 0)}")
    
    # Подпись
    p.setFont("Times-Roman", 8)
    p.drawString(50, 50, "Report generated automatically")
    p.drawString(50, 35, f"Generation date: {timezone.now().strftime('%d.%m.%Y %H:%M')}")
    
    p.showPage()
    p.save()
    
    return response 