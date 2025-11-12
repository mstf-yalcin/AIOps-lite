package com.spring.microservices.accounts.service;

import com.spring.microservices.accounts.constants.AccountsConstants;
import com.spring.microservices.accounts.dto.AccountsDto;
import com.spring.microservices.accounts.dto.CustomerDto;
import com.spring.microservices.accounts.entity.Accounts;
import com.spring.microservices.accounts.entity.Customer;
import com.spring.microservices.accounts.exception.NotFoundException;
import com.spring.microservices.accounts.mapper.AccountsMapper;
import com.spring.microservices.accounts.mapper.CustomerMapper;
import com.spring.microservices.accounts.repository.AccountsRepository;
import com.spring.microservices.accounts.repository.CustomerRepository;
import org.springframework.stereotype.Service;

@Service
public class AccountsService {

    private final AccountsRepository accountsRepository;
    private final CustomerRepository customerRepository;

    public AccountsService(AccountsRepository accountsRepository, CustomerRepository customerRepository) {
        this.accountsRepository = accountsRepository;
        this.customerRepository = customerRepository;
    }


    public CustomerDto create(CustomerDto customerDto) {

        Customer customer = CustomerMapper.toEntity(customerDto);
//        Optional<Customer> optionalCustomer = customerRepository.findByMobileNumber(customerDto.getMobileNumber());
//
//        if(optionalCustomer.isPresent()) {
//            throw new CustomerAlreadyExistsException("Customer already registered with given mobileNumber "
//                    +customerDto.getMobileNumber());
//        }

        Accounts newAccount = createNewAccount(customer);
        customer.setAccounts(newAccount);
        Customer savedCustomer = customerRepository.save(customer);

        return CustomerMapper.toDto(savedCustomer);
    }

    public CustomerDto getCustomerByMobileNumber(String mobileNumber) {
        Customer customer = customerRepository.findByMobileNumber(mobileNumber).orElseThrow(
                () -> new NotFoundException("Customer", "mobileNumber", mobileNumber)
        );
        Accounts accounts = accountsRepository.findByCustomerId(customer.getId()).orElseThrow(
                () -> new NotFoundException("Account", "customerId", customer.getId().toString())
        );
        CustomerDto customerDto = CustomerMapper.toDto(customer);
        customerDto.setAccountsDto(AccountsMapper.toDto(accounts));
        return customerDto;
    }


    public CustomerDto updateAccount(CustomerDto customerDto) {
        AccountsDto accountsDto = customerDto.getAccountsDto();
        Accounts accounts = accountsRepository.findById(accountsDto.getAccountNumber()).orElseThrow(
                () -> new NotFoundException("Account", "AccountNumber", accountsDto.getAccountNumber().toString())
        );
        accounts.setAccountType(accountsDto.getAccountType());
        accounts.setBranchAddress(accountsDto.getBranchAddress());
        accounts.setAccountType(accountsDto.getAccountType());

        Long customerId = accounts.getCustomer().getId();
        Customer customer = customerRepository.findById(customerId).orElseThrow(
                () -> new NotFoundException("Customer", "CustomerID", customerId.toString())
        );

        customer.setAccounts(accounts);
        customer.setName(customerDto.getName());
        customer.setMobileNumber(customerDto.getMobileNumber());
        customer.setEmail(customerDto.getEmail());
        Customer updatedCustomer = customerRepository.save(customer);

        return CustomerMapper.toDto(updatedCustomer);
    }

    public boolean deleteAccount(String mobileNumber) {
        Customer customer = customerRepository.findByMobileNumber(mobileNumber).orElseThrow(
                () -> new NotFoundException("Customer", "mobileNumber", mobileNumber)
        );
        customerRepository.deleteById(customer.getId());
        return true;
    }


    private Accounts createNewAccount(Customer customer) {
        Accounts newAccount = new Accounts();
        newAccount.setCustomer(customer);

        newAccount.setAccountType(AccountsConstants.SAVINGS);
        newAccount.setBranchAddress(AccountsConstants.ADDRESS);
        return newAccount;
    }


}
