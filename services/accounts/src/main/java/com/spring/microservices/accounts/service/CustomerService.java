package com.spring.microservices.accounts.service;

import com.spring.microservices.accounts.dto.CustomerDetailsDto;
import com.spring.microservices.accounts.entity.Accounts;
import com.spring.microservices.accounts.entity.Customer;
import com.spring.microservices.accounts.exception.NotFoundException;
import com.spring.microservices.accounts.mapper.AccountsMapper;
import com.spring.microservices.accounts.mapper.CustomerMapper;
import com.spring.microservices.accounts.repository.AccountsRepository;
import com.spring.microservices.accounts.repository.CustomerRepository;
import com.spring.microservices.accounts.service.client.CardsFeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;

@Service
public class CustomerService {

    private final AccountsRepository accountsRepository;
    private final CustomerRepository customerRepository;
    private final CardsFeignClient cardsFeignClient;

    public CustomerService(AccountsRepository accountsRepository, CustomerRepository customerRepository, CardsFeignClient cardsFeignClient) {
        this.accountsRepository = accountsRepository;
        this.customerRepository = customerRepository;
        this.cardsFeignClient = cardsFeignClient;
    }

    //add correlationId
    public CustomerDetailsDto getCustomerByMobileNumber(String mobileNumber) {
        Customer customer = customerRepository.findByMobileNumber(mobileNumber).orElseThrow(
                () -> new NotFoundException("Customer", "mobileNumber", mobileNumber)
        );
        Accounts accounts = accountsRepository.findByCustomerId(customer.getId()).orElseThrow(
                () -> new NotFoundException("Account", "customerId", customer.getId().toString())
        );
        CustomerDetailsDto customerDetailsDto = CustomerMapper.toCustomerDetailsDto(customer);
        customerDetailsDto.setAccountsDto(AccountsMapper.toDto(accounts));


        ResponseEntity<String> data = cardsFeignClient.getData(mobileNumber);

        if (data != null) {
            customerDetailsDto.setCards(data.getBody());
        }

        return customerDetailsDto;
    }
}
