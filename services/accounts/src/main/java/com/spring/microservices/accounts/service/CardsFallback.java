package com.spring.microservices.accounts.service;

import com.spring.microservices.accounts.service.client.CardsFeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;

@Component
public class CardsFallback implements CardsFeignClient {
    @Override
    public ResponseEntity<String> getData(String phoneNumber) {
        return null;
    }
}
