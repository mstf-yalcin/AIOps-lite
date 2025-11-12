package com.spring.microservices.cards.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class TestController {

    @GetMapping("get/{id}")
    public ResponseEntity<String> getData(@PathVariable String id) {
        return ResponseEntity.ok("Cards: " + id);
    }

}
